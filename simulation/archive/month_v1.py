#!/usr/bin/env python3
"""Offline synthetic queue generator; no database writes or external dependencies."""
import argparse
import collections
import datetime as dt
import hashlib
import heapq
import json
import math
import random
import statistics
from pathlib import Path
from zoneinfo import ZoneInfo

LONDON = ZoneInfo('Europe/London')
# Explicit fictional assumptions, not clinical statistics or diagnostic rules.
ASSUMPTIONS = {
    'fracture_sprain_or_dislocation': (.22, 60, 60),
    'cuts_or_wounds': (.12, 40, 30),
    'head_injury_or_neurological_symptoms': (.30, 75, 80),
    'breathing_problems': (.30, 65, 55),
    'chest_pain_or_heart_symptoms': (.35, 80, 70),
    'abdominal_or_stomach_problems': (.18, 70, 65),
    'other_or_uncategorised': (.10, 45, 0),
    'unknown': (.10, 50, 0),
}

def timestamp(value):
    return dt.datetime.fromisoformat(value).timestamp()

def iso(value):
    return dt.datetime.fromtimestamp(value, LONDON).isoformat()

def seeded(seed, key):
    digest = hashlib.sha256(f'{seed}:{key}'.encode()).digest()
    return random.Random(int.from_bytes(digest[:16], 'big'))

def label_patients(visits, seed):
    result = []
    for v in visits:
        probability = ASSUMPTIONS[v['complaint_category']][0]
        row = {k: v[k] for k in ('visit_id', 'hospital_id', 'arrival_at', 'complaint_category', 'required_specialty_for_demo_model')}
        row['likely_bed_occupancy'] = seeded(seed, v['visit_id']).random() < probability
        result.append(row)
    return result

def durations(visits, seed, run):
    result = {}
    sigma = math.sqrt(math.log(1 + .35 ** 2))
    for v in visits:
        rng = seeded(f'{seed}:run:{run}', v['visit_id'])
        _, general, specialist = ASSUMPTIONS[v['complaint_category']]
        # Means are clinician service times, NOT waits. Keep the sampled work positive.
        sample = lambda mean: max(1.0, rng.lognormvariate(math.log(mean) - sigma*sigma/2, sigma)) if mean else 0.0
        result[v['visit_id']] = (sample(general)*60, sample(specialist)*60)
    return result

def simulate(visits, snapshots, service_times):
    """One hospital. Nonpreemptive priority; specialists follow general assessment.

    A true bed flag also implies priority ONLY under the agreed toy assumption.
    Capacity reductions never interrupt ongoing work. The final shift is held
    until the remaining month-end queue clears.
    """
    assert snapshots and visits
    events, sequence = [], 0
    def event(at, kind, payload):
        nonlocal sequence
        # Finish work, then update capacity, then accept arrivals at identical times.
        order = {'general_done': 0, 'specialist_done': 0, 'snapshot': 1, 'arrival': 2}[kind]
        heapq.heappush(events, (at, order, sequence, kind, payload)); sequence += 1
    for s in snapshots:
        event(timestamp(s['snapshot_at']), 'snapshot', s)
    for i, v in enumerate(visits):
        event(timestamp(v['arrival_at']), 'arrival', i)
    general_queue, specialist_queues = [], collections.defaultdict(list)
    general_busy, beds_busy = 0, 0
    specialist_busy = collections.Counter()
    capacity = None
    first, completed, measurements = {}, {}, []
    def priority(i):
        v = visits[i]
        return (0 if v['likely_bed_occupancy'] else 1, timestamp(v['arrival_at']), v['visit_id'], i)
    while events:
        now, _, _, kind, payload = heapq.heappop(events)
        if kind == 'snapshot':
            capacity = payload
            measurements.append({
                'snapshot_id': payload['snapshot_id'],
                'general_doctors_free': max(0, payload['general_doctors_available'] - general_busy),
                'beds_free': max(0, payload['beds_available'] - beds_busy),
                'waiting_for_first_doctor': len(general_queue),
                'waiting_for_specialist': sum(map(len, specialist_queues.values())),
            })
        elif kind == 'arrival':
            heapq.heappush(general_queue, priority(payload))
        elif kind == 'general_done':
            i = payload; v = visits[i]; general_busy -= 1
            if service_times[v['visit_id']][1] > 0:
                heapq.heappush(specialist_queues[v['required_specialty_for_demo_model']], priority(i))
            else:
                beds_busy -= int(v['likely_bed_occupancy']); completed[v['visit_id']] = now
        else:
            i = payload; v = visits[i]
            specialist_busy[v['required_specialty_for_demo_model']] -= 1
            beds_busy -= int(v['likely_bed_occupancy']); completed[v['visit_id']] = now
        if capacity is None:
            continue
        for specialty, queue in specialist_queues.items():
            available = capacity['specialty_doctors_available'].get(specialty, 0)
            while queue and specialist_busy[specialty] < available:
                i = heapq.heappop(queue)[-1]
                specialist_busy[specialty] += 1
                event(now + service_times[visits[i]['visit_id']][1], 'specialist_done', i)
        blocked = []
        while general_queue and general_busy < capacity['general_doctors_available']:
            entry = heapq.heappop(general_queue); i = entry[-1]; v = visits[i]
            if v['likely_bed_occupancy'] and beds_busy >= capacity['beds_available']:
                blocked.append(entry); continue
            general_busy += 1; beds_busy += int(v['likely_bed_occupancy'])
            first[v['visit_id']] = now
            event(now + service_times[v['visit_id']][0], 'general_done', i)
        for entry in blocked:
            heapq.heappush(general_queue, entry)
        assert general_busy >= 0 and beds_busy >= 0 and all(n >= 0 for n in specialist_busy.values())
    if len(first) != len(visits) or len(completed) != len(visits):
        raise ValueError('Resources cannot clear the queue; no finite wait can be generated for every patient')
    return {
        'waits': {v['visit_id']: (first[v['visit_id']] - timestamp(v['arrival_at'])) / 60 for v in visits},
        'completed_at': completed,
        'snapshots': measurements,
    }

def aggregate_patient(patient, values):
    """Ceiling is applied AFTER averaging all runs, never to individual samples."""
    mean = math.ceil(statistics.mean(values))
    return {**patient,
        'mean_wait_to_first_doctor_minutes': mean,
        'mean_first_doctor_at': iso(timestamp(patient['arrival_at']) + mean*60),
        'min_wait_to_first_doctor_minutes': min(values),
        'max_wait_to_first_doctor_minutes': max(values),
        'wait_stddev_minutes': statistics.stdev(values) if len(values) > 1 else 0,
        'simulation_waits_minutes': values,
        'simulation_run_count': len(values),
    }

def generate(data, seed=20261024, runs=5):
    assert data['dataset_metadata']['synthetic_data'] is True
    patients = label_patients(data['visits'], seed)
    by_hospital = collections.defaultdict(list)
    for v in patients:
        by_hospital[v['hospital_id']].append(v)
    snapshot_groups = collections.defaultdict(list)
    for s in data['staffing_snapshots']:
        snapshot_groups[s['hospital_id']].append(s)
    samples = collections.defaultdict(list)
    snapshots = collections.defaultdict(list)
    run_summaries = []
    for run in range(1, runs+1):
        work = durations(patients, seed, run)
        all_waits = []
        drain = 0
        for hospital_id, visits in sorted(by_hospital.items()):
            result = simulate(visits, snapshot_groups[hospital_id], work)
            for visit_id, wait in result['waits'].items():
                samples[visit_id].append(wait); all_waits.append(wait)
            for measurement in result['snapshots']:
                snapshots[measurement['snapshot_id']].append(measurement)
            drain = max(drain, max(result['completed_at'].values()))
        run_summaries.append({'run': run, 'mean_wait_minutes': statistics.mean(all_waits), 'max_wait_minutes': max(all_waits), 'last_completion_at': iso(drain)})
        print(f'Run {run}/{runs}: {len(all_waits)} patients, mean wait {statistics.mean(all_waits):.2f} minutes', flush=True)
    output_visits = [aggregate_patient(v, samples[v['visit_id']]) for v in patients]
    snapshot_output = []
    for s in data['staffing_snapshots']:
        hospital_visits = by_hospital[s['hospital_id']]
        at = timestamp(s['snapshot_at'])
        prior_arrivals = sum(at-3600 <= timestamp(v['arrival_at']) < at for v in hospital_visits)
        measurements = snapshots[s['snapshot_id']]
        snapshot_output.append({k: val for k, val in s.items() if k not in ('patients_waiting_for_doctor_referral','patients_waiting_for_diagnosis','simulated_staffing_status','staffing_status_basis')} | {
            'observed_arrivals_last_hour': prior_arrivals,
            'mean_general_doctors_free': statistics.mean(r['general_doctors_free'] for r in measurements),
            'mean_beds_free': statistics.mean(r['beds_free'] for r in measurements),
            'mean_waiting_for_first_doctor': statistics.mean(r['waiting_for_first_doctor'] for r in measurements),
            'mean_waiting_for_specialist': statistics.mean(r['waiting_for_specialist'] for r in measurements),
        })
    daily = collections.defaultdict(lambda: {'visits': 0, 'priority_bed_cases': 0, 'expected_priority_bed_cases': 0.0})
    for v in patients:
        day = dt.datetime.fromisoformat(v['arrival_at']).astimezone(LONDON).date().isoformat()
        row = daily[(v['hospital_id'], day)]
        row['visits'] += 1
        row['priority_bed_cases'] += int(v['likely_bed_occupancy'])
        row['expected_priority_bed_cases'] += ASSUMPTIONS[v['complaint_category']][0]
    totals = [r['mean_wait_to_first_doctor_minutes'] for r in output_visits]
    summary = {
        'patients': len(patients), 'runs': runs, 'patient_runs_completed': len(patients)*runs,
        'mean_patient_wait_minutes': statistics.mean(totals),
        'unrounded_mean_patient_wait_minutes': statistics.mean(statistics.mean(r['simulation_waits_minutes']) for r in output_visits),
        'median_patient_mean_wait_minutes': statistics.median(totals),
        'max_patient_mean_wait_minutes': max(totals),
        'patients_with_any_wait': sum(w > 0 for w in totals),
        'priority_bed_cases': sum(v['likely_bed_occupancy'] for v in patients),
        'run_summaries': run_summaries,
        'daily_counts': [{'hospital_id': h, 'date': d, **val} for (h,d),val in sorted(daily.items())],
    }
    result = {
        'dataset_metadata': {
            'synthetic_data': True, 'model_version': 'resource_queue_simulation_v1', 'seed': seed,
            'date_range': data['dataset_metadata']['date_range'], 'timezone': 'Europe/London',
            'simulation_runs': runs, 'same_patients_and_arrivals_across_runs': True,
            'mean_wait_rounding': 'Ceiling of each patient arithmetic mean across runs, stored as integer minutes; first-doctor mean timestamp uses that rounded duration.',
            'notice': 'Invented simulation, not real hospital operations or clinical triage. Bed-use flag implies priority only under a fictional demo assumption.',
            'initial_state': 'Empty queues and all rostered resources free at the first snapshot; no warm-up.',
            'end_state': 'Drain remaining patients using final snapshot staffing, without adding arrivals after the source month.',
            'capacity_semantics': 'Source doctors and beds are treated as total available capacity, not free-resource counts; calculated free capacity is reported separately.',
            'priority_semantics': 'Priority known at arrival for this simulation; clinical triage duration is not modelled. Nonpreemptive, no interruption of ongoing treatment.',
            'specialist_semantics': 'Specialist review follows initial general-doctor contact. Scarcity delays first contact indirectly by holding treatment spaces for bed-flagged patients.',
            'repeated_variables': 'Only general and specialist service durations change across runs. Staffing, bed capacity, arrivals, categories and flags stay fixed.',
            'service_time_distribution': 'Lognormal, coefficient of variation 0.35; minimum 1 minute.',
            'category_assumptions': {k: {'fictional_priority_bed_probability': a, 'mean_general_service_minutes': b, 'mean_specialist_service_minutes': c} for k,(a,b,c) in ASSUMPTIONS.items()},
        },
        'hospitals': [{k: h[k] for k in ('hospital_id','name','address','latitude','longitude')} for h in data['hospitals']],
        'visits': output_visits, 'staffing_snapshots': snapshot_output,
    }
    return result, summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output_directory', type=Path)
    parser.add_argument('--seed', type=int, default=20261024)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    out = args.output_directory / 'queuecare_simulated_month.json'
    report = args.output_directory / 'summary.json'
    if out.exists() or report.exists():
        parser.error('Output exists; use a fresh directory to preserve prior results')
    raw = args.source.read_bytes()
    result, summary = generate(json.loads(raw), args.seed)
    result['dataset_metadata']['source_sha256'] = hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result, separators=(',', ':')))
    report.write_text(json.dumps(summary, indent=2))
    print(f'Results: {out}\nSummary: {report}')

if __name__ == '__main__':
    main()
