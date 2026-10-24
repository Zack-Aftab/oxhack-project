#!/usr/bin/env python3
"""Resource queue model v2: reproducible synthetic scenarios, never real NHS data."""
import argparse
import bisect
import collections
import csv
import datetime as dt
import hashlib
import heapq
import json
import math
import random
import statistics
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Europe/London')
SHARES = [.08, .06, .20, .24, .26, .16]
DOCTORS = [4, 4, 8, 10, 10, 6]
NURSES = [2, 2, 3, 3, 3, 2]
WEEKDAY = [.99, 1.00, 1.00, 1.00, 1.04, 1.02, .95]
# Relative case complexity and flag probabilities are explicitly invented.
CASE = {
    'fracture_sprain_or_dislocation': (.22, 20),
    'cuts_or_wounds': (.12, 15),
    'head_injury_or_neurological_symptoms': (.30, 25),
    'breathing_problems': (.30, 25),
    'chest_pain_or_heart_symptoms': (.35, 30),
    'abdominal_or_stomach_problems': (.18, 25),
    'other_or_uncategorised': (.10, 15),
    'unknown': (.10, 20),
}


def ts(s):
    return dt.datetime.fromisoformat(s).timestamp()


def iso(t):
    return dt.datetime.fromtimestamp(t, ZONE).isoformat()


def rng_for(seed, key):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{key}'.encode()).digest()[:16], 'big'))


def lognormal(rng, mean, cv):
    if mean == 0:
        return 0.0
    sigma = math.sqrt(math.log1p(cv*cv))
    return rng.lognormvariate(math.log(mean)-sigma*sigma/2, sigma)


def percentile(values, p):
    a = sorted(values)
    at = (len(a)-1)*p
    lo = math.floor(at); hi = math.ceil(at)
    return a[lo] + (a[hi]-a[lo])*(at-lo)


def stats(values):
    return {'mean': statistics.mean(values), 'median': statistics.median(values),
            'p90': percentile(values, .9), 'p95': percentile(values, .95),
            'max': max(values), 'fraction_over_60_minutes': sum(v>60 for v in values)/len(values),
            'fraction_over_240_minutes': sum(v>240 for v in values)/len(values)}


def configure(source):
    counts = (collections.Counter({v['complaint_category']:v['count'] for v in source['case_mix']})
              if 'case_mix' in source else collections.Counter(v['complaint_category'] for v in source['visits']))
    total = sum(counts.values())
    probabilities = {k: counts[k]/total for k in sorted(counts)}
    flag_average = sum(probabilities[k]*CASE[k][0] for k in probabilities)
    service_average = sum(probabilities[k]*CASE[k][1] for k in probabilities)
    special = {v['complaint_category']: v['required_specialty_for_demo_model'] for v in source.get('case_mix',source.get('visits',[]))}
    eligible = sum(p for k,p in probabilities.items() if special[k] != 'emergency_medicine')
    return {'probabilities': probabilities, 'specialties': special,
            'flag_probabilities': {k: CASE[k][0]*.20/flag_average for k in probabilities},
            'general_mean_minutes': {k: CASE[k][1]*20/service_average for k in probabilities},
            'specialist_review_probability_if_eligible': .25/eligible}


def generate_population(hospitals, start, end, config, seed, extra=False):
    """NHPP by 4h block, with shared daily variation. Additional stream for +20%."""
    patients = []
    warmup_start = start - dt.timedelta(days=3)
    categories = list(config['probabilities'])
    weights = list(config['probabilities'].values())
    day = warmup_start
    while day < end:
        for hospital in hospitals:
            hid = hospital['hospital_id']
            daily = lognormal(rng_for(seed, f'day:{hid}:{day.date()}'), 1, .08)
            daily_mean = 450 * WEEKDAY[day.weekday()] * daily * (.2 if extra else 1)
            for block, share in enumerate(SHARES):
                rng = rng_for(seed, f'arrivals:{hid}:{day.date()}:{block}:{extra}')
                begin = (day + dt.timedelta(hours=block*4)).timestamp()
                time = begin
                while True:
                    time += rng.expovariate(daily_mean*share/(4*3600))
                    if time >= begin+4*3600:
                        break
                    category = rng.choices(categories, weights, k=1)[0]
                    vid = f'{hid}-{day.date()}-B{block}-{"X" if extra else "P"}{len(patients):06}'
                    labels = rng_for(seed, f'labels:{vid}')
                    flag = labels.random() < config['flag_probabilities'][category]
                    specialty = config['specialties'][category]
                    review = specialty != 'emergency_medicine' and labels.random() < config['specialist_review_probability_if_eligible']
                    patients.append({'visit_id': vid, 'hospital_id': hid, 'arrival_at': iso(time),
                                     'complaint_category': category, 'required_specialty_for_demo_model': specialty,
                                     'likely_bed_occupancy': flag, 'requires_specialist_review': review,
                                     'is_warmup': day < start})
        day += dt.timedelta(days=1)
    return sorted(patients, key=lambda v: (v['arrival_at'], v['visit_id']))


def make_schedule(hospital_id, start, end, specialties, doctor_scale=1, beds=20, doctor_delta=0, doctor_roster=None):
    # Continue changing shifts after arrivals stop, to drain the last patients.
    rows = []
    t = start-dt.timedelta(days=3)
    while t < end+dt.timedelta(days=7):
        block = t.hour//4
        rows.append({'snapshot_id': f'{hospital_id}-{t.strftime("%Y%m%dT%H")}',
                     'hospital_id': hospital_id, 'snapshot_at': t.isoformat(),
                     'staffing_window_end': (t+dt.timedelta(hours=1)).isoformat(),
                     'general_doctors_available': max(1, math.floor((doctor_roster or DOCTORS)[block]*doctor_scale)+doctor_delta),
                     'triage_nurses_available': NURSES[block], 'beds_available': beds,
                     # One concurrent shared on-call review per specialty, not ED headcount.
                     'specialty_doctors_available': {s: 1 for s in specialties}})
        t += dt.timedelta(hours=1)
    return rows


def draw_work(visits, config, seed, run):
    result = {}
    for v in visits:
        rng = rng_for(seed, f'work:{run}:{v["visit_id"]}')
        result[v['visit_id']] = {
            'triage': lognormal(rng, 4.5, .45)*60,
            'general': lognormal(rng, config['general_mean_minutes'][v['complaint_category']], .60)*60,
            'specialist': lognormal(rng, 20, .50)*60 if v['requires_specialist_review'] else 0,
            'response': lognormal(rng, 30, .70)*60 if v['requires_specialist_review'] else 0,
            'bed_hold': lognormal(rng, 240, .65)*60 if v['likely_bed_occupancy'] else 0,
        }
    return result


def run_hospital(visits, schedule, work, measured_start, measured_end, priority_field="likely_bed_occupancy", triage_priority=False):
    events = []; counter = 0
    def push(time, kind, value):
        nonlocal counter
        order = 1 if kind == 'snapshot' else 2 if kind == 'arrival' else 0
        heapq.heappush(events, (time, order, counter, kind, value)); counter += 1
    for i,v in enumerate(visits):
        push(ts(v['arrival_at']), 'arrival', i)
    for s in schedule:
        push(ts(s['snapshot_at']), 'snapshot', s)
    triage_queue = [] if triage_priority else collections.deque(); general_queue = []; specialist_queue = collections.defaultdict(list)
    triage_busy = general_busy = bed_busy = 0
    specialist_busy = collections.Counter()
    first = {}; triaged = {}; departed = {}; general_done = set(); specialist_done = set(); hold_done = set()
    capacity = None; observations = []
    integral = collections.Counter(); previous = events[0][0]
    specialist_waits = []
    spec_requested = {}
    def priority(i):
        return (0 if visits[i].get(priority_field, False) else 1, ts(visits[i]['arrival_at']), visits[i]['visit_id'], i)
    def release_if_finished(i, now):
        nonlocal bed_busy
        if i not in departed and i in general_done and i in specialist_done and i in hold_done:
            bed_busy -= int(visits[i]['likely_bed_occupancy']); departed[i] = now
    while events:
        now, _, _, kind, value = heapq.heappop(events)
        duration = max(0, min(now, measured_end)-max(previous, measured_start))
        if capacity and duration:
            integral['doctor_busy_seconds'] += duration*general_busy
            integral['doctor_capacity_seconds'] += duration*capacity['general_doctors_available']
            integral['bed_busy_seconds'] += duration*bed_busy
            integral['bed_capacity_seconds'] += duration*capacity['beds_available']
            integral['triage_busy_seconds'] += duration*triage_busy
            integral['triage_capacity_seconds'] += duration*capacity['triage_nurses_available']
            integral['specialist_busy_seconds'] += duration*sum(specialist_busy.values())
            integral['specialist_capacity_seconds'] += duration*sum(capacity['specialty_doctors_available'].values())
            integral['general_queue_seconds'] += duration*len(general_queue)
            integral['triage_queue_seconds'] += duration*len(triage_queue)
            integral['bed_full_seconds'] += duration*(bed_busy >= capacity['beds_available'])
        previous = now
        if kind == 'snapshot':
            capacity = value
            if measured_start <= now < measured_end:
                observations.append({**value,
                    'general_doctors_free': max(0, capacity['general_doctors_available']-general_busy),
                    'beds_free': max(0, capacity['beds_available']-bed_busy),
                    'waiting_for_first_doctor': len(general_queue),
                    'waiting_for_triage': len(triage_queue),
                    'waiting_for_specialist': sum(map(len, specialist_queue.values())),
                    'specialty_doctors_free': {s: max(0,n-specialist_busy[s]) for s,n in capacity['specialty_doctors_available'].items()},
                })
        elif kind == 'arrival':
            if triage_priority:
                heapq.heappush(triage_queue, priority(value))
            else:
                triage_queue.append(value)
        elif kind == 'triaged':
            triage_busy -= 1; triaged[value] = now
            heapq.heappush(general_queue, priority(value))
        elif kind == 'general_done':
            i = value; general_busy -= 1; general_done.add(i)
            if visits[i]['requires_specialist_review']:
                specialty = visits[i]['required_specialty_for_demo_model']
                heapq.heappush(specialist_queue[specialty], priority(i)); spec_requested[i] = now
            else:
                specialist_done.add(i)
            release_if_finished(i, now)
        elif kind == 'specialist_done':
            i = value; specialty = visits[i]['required_specialty_for_demo_model']
            specialist_busy[specialty] -= 1; specialist_done.add(i); release_if_finished(i, now)
        elif kind == 'hold_done':
            hold_done.add(value); release_if_finished(value, now)
        if capacity is None:
            continue
        # First complete triage; only then may the assigned flag give queue priority.
        while triage_queue and triage_busy < capacity['triage_nurses_available']:
            i = heapq.heappop(triage_queue)[-1] if triage_priority else triage_queue.popleft()
            triage_busy += 1
            push(now+work[visits[i]['visit_id']]['triage'], 'triaged', i)
        for specialty, queue in specialist_queue.items():
            while queue and specialist_busy[specialty] < capacity['specialty_doctors_available'].get(specialty,0):
                i = heapq.heappop(queue)[-1]; specialist_busy[specialty] += 1
                w = work[visits[i]['visit_id']]
                if not visits[i]['is_warmup']:
                    specialist_waits.append((now-spec_requested[i]+w['response'])/60)
                # Access response time occupies the consultation slot: conservative shared-access approximation.
                push(now+w['response']+w['specialist'], 'specialist_done', i)
        blocked = []
        while general_queue and general_busy < capacity['general_doctors_available']:
            entry = heapq.heappop(general_queue); i = entry[-1]; v = visits[i]
            if v['likely_bed_occupancy'] and bed_busy >= capacity['beds_available']:
                blocked.append(entry); continue
            first[i] = now; general_busy += 1; bed_busy += int(v['likely_bed_occupancy'])
            w = work[v['visit_id']]
            push(now+w['general'], 'general_done', i)
            if v['likely_bed_occupancy']:
                push(now+w['bed_hold'], 'hold_done', i)
            else:
                hold_done.add(i)
        for entry in blocked:
            heapq.heappush(general_queue, entry)
        assert min(triage_busy, general_busy, bed_busy) >= 0
        assert all(n >= 0 for n in specialist_busy.values())
        assert bed_busy <= capacity['beds_available']
    if len(first) != len(visits) or len(departed) != len(visits):
        raise ValueError('A required resource never became available; not every patient completed')
    results = {}
    for i,v in enumerate(visits):
        assert ts(v['arrival_at']) <= triaged[i] <= first[i] <= departed[i]
        if not v['is_warmup']:
            results[v['visit_id']] = {
                'wait_minutes': (first[i]-ts(v['arrival_at']))/60,
                'triage_elapsed_minutes': (triaged[i]-ts(v['arrival_at']))/60,
                'departure_at': departed[i],
            }
    return results, observations, dict(integral), specialist_waits


def run_scenario(visits, hospitals, start, end, config, seed, name, doctor_scale=1, beds=20, runs=5, keep_snapshots=True, doctor_delta=0, priority_field="likely_bed_occupancy", general_work_multiplier=1, doctor_roster=None, triage_priority=False, bed_hold_multiplier=1):
    groups = {h['hospital_id']: [] for h in hospitals}
    for v in visits:
        groups[v['hospital_id']].append(v)
    specialties = sorted(set(config['specialties'].values())-{'emergency_medicine'})
    samples = collections.defaultdict(list); observations = collections.defaultdict(list)
    runs_summary = []; overall_integrals = collections.Counter(); triage_samples = []; specialist_samples = []
    for run in range(1,runs+1):
        work = draw_work(visits, config, seed, run)
        for row in work.values():
            row["general"] *= general_work_multiplier
            row["bed_hold"] *= bed_hold_multiplier
        integral = collections.Counter(); values = []; last_departure = 0
        for h in hospitals:
            hid = h['hospital_id']
            schedule = make_schedule(hid, start, end, specialties, doctor_scale, beds, doctor_delta, doctor_roster)
            result, snaps, totals, specialist_waits = run_hospital(groups[hid], schedule, work, start.timestamp(), end.timestamp(), priority_field=priority_field, triage_priority=triage_priority)
            integral.update(totals); specialist_samples.extend(specialist_waits)
            for vid, row in result.items():
                samples[vid].append(row['wait_minutes']); values.append(row['wait_minutes']); triage_samples.append(row['triage_elapsed_minutes'])
                last_departure = max(last_departure, row['departure_at'])
            if keep_snapshots:
                for snap in snaps:
                    observations[snap['snapshot_id']].append(snap)
        overall_integrals.update(integral)
        runs_summary.append({'run': run, **stats(values), 'last_departure_at': iso(last_departure),
                             'doctor_utilisation': integral['doctor_busy_seconds']/integral['doctor_capacity_seconds'],
                             'bed_utilisation': integral['bed_busy_seconds']/integral['bed_capacity_seconds']})
        print(f'{name} run {run}/{runs}: n={len(values)}, mean={statistics.mean(values):.2f}, median={statistics.median(values):.2f}', flush=True)
    measured = [v for v in visits if not v['is_warmup']]
    output = []
    for v in measured:
        row = {k:val for k,val in v.items() if k != 'is_warmup'}
        values = samples[v['visit_id']]; raw = statistics.mean(values); rounded = math.ceil(raw)
        output.append({**row, 'mean_wait_to_first_doctor_minutes': rounded,
                       'mean_first_doctor_at': iso(ts(v['arrival_at'])+rounded*60),
                       'simulation_waits_minutes': values, 'simulation_run_count': runs,
                       'min_wait_to_first_doctor_minutes': min(values), 'max_wait_to_first_doctor_minutes': max(values),
                       'wait_stddev_minutes': statistics.stdev(values) if runs>1 else 0})
    all_samples = [w for row in samples.values() for w in row]
    raw_patient_means = [statistics.mean(row) for row in samples.values()]
    rounded_means = [v['mean_wait_to_first_doctor_minutes'] for v in output]
    daily = collections.defaultdict(lambda: {'arrivals':0,'priority_bed_cases':0,'expected_priority_bed_cases':0.0})
    for v in measured:
        key = (v['hospital_id'],dt.datetime.fromisoformat(v['arrival_at']).date().isoformat())
        daily[key]['arrivals'] += 1; daily[key]['priority_bed_cases'] += int(v['likely_bed_occupancy'])
        daily[key]['expected_priority_bed_cases'] += config['flag_probabilities'][v['complaint_category']]
    summary = {'scenario': name, 'patients':len(measured), 'warmup_patients':len(visits)-len(measured), 'runs':runs,
               'patient_runs':len(measured)*runs, 'pooled_run_waits':stats(all_samples),
               'unrounded_patient_means':stats(raw_patient_means), 'stored_integer_patient_means':stats(rounded_means),
               'triage_elapsed_minutes':stats(triage_samples),
               'specialist_wait_after_referral_minutes': stats(specialist_samples) if specialist_samples else None,
               'doctor_utilisation':overall_integrals['doctor_busy_seconds']/overall_integrals['doctor_capacity_seconds'],
               'bed_utilisation':overall_integrals['bed_busy_seconds']/overall_integrals['bed_capacity_seconds'],
               'triage_utilisation':overall_integrals['triage_busy_seconds']/overall_integrals['triage_capacity_seconds'],
               'specialist_slot_utilisation':overall_integrals['specialist_busy_seconds']/overall_integrals['specialist_capacity_seconds'] if overall_integrals['specialist_capacity_seconds'] else None,
               'fraction_of_time_beds_full':overall_integrals['bed_full_seconds']/(runs*len(hospitals)*(end-start).total_seconds()),
               'runs_summary':runs_summary, 'daily_counts':[{'hospital_id':hid,'date':day,**row} for (hid,day),row in sorted(daily.items())],
               'by_hospital':[], 'by_priority':[]}
    for h in hospitals:
        subset=[v for v in output if v['hospital_id']==h['hospital_id']]
        summary['by_hospital'].append({'hospital_id':h['hospital_id'],'name':h['name'],'patients':len(subset),
                                       **stats([statistics.mean(v['simulation_waits_minutes']) for v in subset])})
    for flag in (True,False):
        subset=[v for v in output if v.get(priority_field, False)==flag]
        summary['by_priority'].append({priority_field:flag,'patients':len(subset),
                                       **stats([statistics.mean(v['simulation_waits_minutes']) for v in subset])})
    snapshot_output=[]
    arrivals_by_hospital={hid: sorted(ts(v['arrival_at']) for v in group) for hid,group in groups.items()}
    for sid, rows in sorted(observations.items()):
        first=rows[0]; at=ts(first['snapshot_at']); arrivals=arrivals_by_hospital[first['hospital_id']]
        row={k:first[k] for k in ('snapshot_id','hospital_id','snapshot_at','staffing_window_end','general_doctors_available','triage_nurses_available','beds_available','specialty_doctors_available')}
        row['observed_arrivals_last_hour']=bisect.bisect_left(arrivals,at)-bisect.bisect_left(arrivals,at-3600)
        for field in ('general_doctors_free','beds_free','waiting_for_first_doctor','waiting_for_triage','waiting_for_specialist'):
            row[f'mean_{field}']=statistics.mean(r[field] for r in rows)
        snapshot_output.append(row)
    return output, snapshot_output, summary


def save_csv(visits,path):
    columns=['visit_id','hospital_id','arrival_at','complaint_category','likely_bed_occupancy','requires_specialist_review','mean_wait_to_first_doctor_minutes','mean_first_doctor_at']+[f'run_{i}_wait_minutes' for i in range(1,6)]
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for v in visits:
            row={k:v[k] for k in columns if k in v}
            row.update({f'run_{i}_wait_minutes':w for i,w in enumerate(v['simulation_waits_minutes'],1)})
            writer.writerow(row)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--seed',type=int,default=20261025)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory; never overwrite a previous simulation')
    args.output.mkdir(parents=True)
    raw=args.source.read_bytes();source=json.loads(raw);assert source['dataset_metadata']['synthetic_data'] is True
    hospitals=[{k:h[k] for k in ('hospital_id','name','address','latitude','longitude')} for h in source['hospitals']]
    start=dt.datetime(2026,9,21,tzinfo=ZONE);end=dt.datetime(2026,10,19,tzinfo=ZONE)
    config=configure(source)
    visits=generate_population(hospitals,start,end,config,args.seed)
    rows,snaps,summary=run_scenario(visits,hospitals,start,end,config,args.seed,'baseline')
    metadata={'synthetic_data':True,'model_version':'resource_queue_simulation_v2','seed':args.seed,
              'source_sha256':hashlib.sha256(raw).hexdigest(),'timezone':'Europe/London',
              'date_range':{'start':'2026-09-21','end':'2026-10-18','inclusive':True},
              'simulation_runs':5,'expected_arrivals_per_hospital_day':450,'daily_noise_cv':.08,
              'weekday_multipliers':WEEKDAY,'four_hour_arrival_shares':SHARES,'effective_general_doctors_by_four_hour_block':DOCTORS,
              'triage_nurses_by_four_hour_block':NURSES,'mean_triage_service_minutes':4.5,
              'mean_general_service_minutes_case_mix_weighted':20,'mean_specialist_service_minutes':20,
              'mean_specialist_access_response_minutes':30,'concurrent_review_slots_per_specialty':1,
              'expected_fraction_receiving_specialist_review':.25,'treatment_spaces':20,'mean_treatment_space_hold_minutes':240,
              'warmup_days':3,'warmup_excluded':True,'same_arrivals_categories_flags_across_runs':True,
              'rounding':'Integer ceiling applied after averaging each patient five unrounded waits',
              'notice':'All operations and probabilities are invented, not hospital measurements. This is an uncalibrated engineering scenario, not validated NHS waiting-time prediction.',
              'priority_assumption':'A true likely_bed_occupancy flag ALSO assigns priority after triage. No clinical equivalence is claimed.',
              'specialist_assumption':'Shared-access review slot is occupied during response plus consultation. Non-bed patients do not occupy modelled treatment spaces.',
              'capacity_assumption':'Doctor numbers represent effective concurrent capacity, not total hospital headcount. No individual shifts, breaks or handovers are modelled.',
              'service_cvs':{'triage':.45,'general':.60,'specialist':.50,'specialist_response':.70,'bed_hold':.65},
              'category_assumptions':config}
    (args.output/'queuecare_simulated_month.json').write_text(json.dumps({'dataset_metadata':metadata,'hospitals':hospitals,'visits':rows,'staffing_snapshots':snaps},separators=(',',':')))
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    save_csv(rows,args.output/'patient_average_waits.csv')
    sensitivities=[]
    for name,delta,beds,pop in [
        ('one_more_general_doctor_per_shift',1,20,visits),
        ('one_fewer_general_doctor_per_shift',-1,20,visits),
        ('four_fewer_treatment_spaces',0,16,visits),
        ('twenty_percent_more_arrivals',0,20,sorted(visits+generate_population(hospitals,start,end,config,args.seed,extra=True),key=lambda v:(v['arrival_at'],v['visit_id']))),
    ]:
        _,_,result=run_scenario(pop,hospitals,start,end,config,args.seed,name,doctor_delta=delta,beds=beds,keep_snapshots=False)
        sensitivities.append(result)
        (args.output/'sensitivity.json').write_text(json.dumps(sensitivities,indent=2))
    print('Saved results:',args.output,flush=True)

if __name__=='__main__':
    main()
