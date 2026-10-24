#!/usr/bin/env python3
"""V3: separate synthetic urgency and bed need. Same cohort as v2, no live writes."""
import argparse
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import math
import statistics
from pathlib import Path

spec = importlib.util.spec_from_file_location('resource_model', Path(__file__).resolve().parents[1]/'engine.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

# Relative probabilities, not clinical evidence or symptom-triage rules.
URGENCY_CATEGORY = {
    'chest_pain_or_heart_symptoms': 2.0,
    'breathing_problems': 1.5,
    'head_injury_or_neurological_symptoms': 1.5,
    'abdominal_or_stomach_problems': 1.0,
    'fracture_sprain_or_dislocation': 1.0,
    'cuts_or_wounds': .5,
    'other_or_uncategorised': .5,
    'unknown': .5,
}
HOUR_MULTIPLIERS = [1.10, 1.15, .90, .90, 1.00, 1.10]
DAY_MULTIPLIERS = [.95, .95, 1, 1, 1.05, 1.05, 1]


def assign_urgency(visits, seed, target=.03):
    scores = []
    for v in visits:
        arrival = dt.datetime.fromisoformat(v['arrival_at']).astimezone(model.ZONE)
        scores.append(URGENCY_CATEGORY[v['complaint_category']] * HOUR_MULTIPLIERS[arrival.hour//4] * DAY_MULTIPLIERS[arrival.weekday()])
    measured = [s for s,v in zip(scores,visits) if not v['is_warmup']]
    scale = target/statistics.mean(measured)
    result = []
    for v,score in zip(visits,scores):
        probability = scale*score
        assert 0 <= probability <= 1
        # A separate random stream leaves bed requirements and other attributes untouched.
        urgent = model.rng_for(seed,f'clinical-priority:{v["visit_id"]}').random() < probability
        result.append({**v,'clinician_urgent':urgent,'synthetic_urgency_probability':probability})
    return result


def check_output(rows):
    ids = set()
    for v in rows:
        assert v['visit_id'] not in ids; ids.add(v['visit_id'])
        values=v['simulation_waits_minutes']
        assert len(values)==5 and all(math.isfinite(w) and w>=0 for w in values)
        assert type(v['mean_wait_to_first_doctor_minutes']) is int
        assert v['mean_wait_to_first_doctor_minutes']==math.ceil(statistics.mean(values))
        assert type(v['clinician_urgent']) is bool and type(v['likely_bed_occupancy']) is bool
        assert abs(model.ts(v['mean_first_doctor_at'])-model.ts(v['arrival_at'])-60*v['mean_wait_to_first_doctor_minutes'])<1e-5


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--seed',type=int,default=20261025)
    args=parser.parse_args()
    if args.output.exists():parser.error('Use a new output directory to preserve earlier results')
    args.output.mkdir(parents=True)
    raw=args.source.read_bytes();source=json.loads(raw)
    assert source['dataset_metadata']['synthetic_data'] is True
    config=model.configure(source)
    hospitals=[{k:h[k] for k in ('hospital_id','name','address','latitude','longitude')} for h in source['hospitals']]
    start=dt.datetime(2026,9,21,tzinfo=model.ZONE);end=dt.datetime(2026,10,19,tzinfo=model.ZONE)
    original=model.generate_population(hospitals,start,end,config,args.seed)
    visits=assign_urgency(original,args.seed)
    rows,snapshots,summary=model.run_scenario(visits,hospitals,start,end,config,args.seed,'separate_3pct_priority',priority_field='clinician_urgent')
    check_output(rows)
    measured=[v for v in visits if not v['is_warmup']]
    assert abs(statistics.mean(v['synthetic_urgency_probability'] for v in measured)-.03)<1e-12
    summary['priority_label_counts']={'urgent':sum(v['clinician_urgent'] for v in measured),
        'bed_required':sum(v['likely_bed_occupancy'] for v in measured),
        'both':sum(v['clinician_urgent'] and v['likely_bed_occupancy'] for v in measured),
        'expected_urgent':sum(v['synthetic_urgency_probability'] for v in measured)}
    # The inherited v2 daily bed counter name is corrected in the new output.
    by_day=collections.defaultdict(lambda:{'arrivals':0,'urgent':0,'bed_required':0,'expected_urgent':0.0})
    for v in measured:
        key=(v['hospital_id'],v['arrival_at'][:10]);row=by_day[key]
        row['arrivals']+=1;row['urgent']+=v['clinician_urgent'];row['bed_required']+=v['likely_bed_occupancy'];row['expected_urgent']+=v['synthetic_urgency_probability']
    summary['daily_counts']=[{'hospital_id':h,'date':d,**r} for (h,d),r in sorted(by_day.items())]
    metadata={'synthetic_data':True,'model_version':'resource_queue_simulation_v3','seed':args.seed,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'date_range':{'start':'2026-09-21','end':'2026-10-18'},'timezone':'Europe/London',
        'endpoint':'Reception to first general A&E doctor contact, including triage; no specialist-care or transfer time added',
        'same_v2_cohort':True,'warmup_days':3,'runs':5,'priority_after_triage':True,
        'priority_semantics':'Separate synthetic clinician_urgent flag; bed requirement does not assign priority',
        'target_expected_highest_priority_fraction':.03,'clinical_evidence_for_urgency_rate':False,
        'urgency_category_relative_weights':URGENCY_CATEGORY,'urgency_four_hour_relative_weights':HOUR_MULTIPLIERS,
        'urgency_weekday_relative_weights':DAY_MULTIPLIERS,'measured_probability_normalisation':True,
        'notice':'Uncalibrated synthetic engineering scenario, not real hospital measurements. 3% represents a chosen highest-priority subgroup, not every NHS urgent triage category.',
        'expected_arrivals_per_site_day':450,'doctors_by_four_hour_block':model.DOCTORS,
        'triage_nurses_by_four_hour_block':model.NURSES,'treatment_spaces':20,'mean_bed_hold_minutes':240,
        'case_mix_weighted_general_service_minutes':20,'rounding':'Ceiling of patient arithmetic mean after five runs',
        'specialist_limitation':'Retains v2 universal six-specialty shared-access approximation; does not implement rare capability gaps or transfers. Do not infer real site suitability.',
        'baseline_unchanged_resources':True,'category_assumptions':config}
    (args.output/'queuecare_simulated_month.json').write_text(json.dumps({'dataset_metadata':metadata,'hospitals':hospitals,'visits':rows,'staffing_snapshots':snapshots},separators=(',',':')))
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    model.save_csv(rows,args.output/'patient_average_waits.csv')
    # Add separate urgency to the derivative CSV; do not hide it in the bed flag.
    import csv
    path=args.output/'patient_average_waits.csv'
    with path.open() as f: reader=csv.DictReader(f);columns=reader.fieldnames;csvrows=list(reader)
    flags={v['visit_id']:v['clinician_urgent'] for v in rows}
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns+['clinician_urgent']);writer.writeheader()
        for row in csvrows:writer.writerow({**row,'clinician_urgent':flags[row['visit_id']]})
    _,_,constrained=model.run_scenario(visits,hospitals,start,end,config,args.seed,'five_percent_more_general_work',
        priority_field='clinician_urgent',general_work_multiplier=1.05,keep_snapshots=False)
    constrained['daily_counts']=summary['daily_counts']
    constrained['priority_label_counts']=summary['priority_label_counts']
    (args.output/'sensitivity.json').write_text(json.dumps(constrained,indent=2))
    (args.output/'validation.json').write_text(json.dumps({'verified_patients':len(rows),'verified_patient_runs':len(rows)*5,'verified_ceiled_integer_means':len(rows),'fixed_cohort':True,'expected_urgent_fraction':.03,'urgency_separate_from_bed_need':True},indent=2))
    print('Saved:',args.output,flush=True)

if __name__=='__main__':main()
