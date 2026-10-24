#!/usr/bin/env python3
"""Thirty measured days after 3 warm-up days; pre-known 5% bed/priority flag."""
import argparse
import collections
import copy
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import math
import statistics
from pathlib import Path

spec=importlib.util.spec_from_file_location('model',Path(__file__).with_name('engine.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Chosen constrained scenario, not measured staffing or a fitted waiting-time target.
DOCTORS=[3,3,8,10,9,6]


def make_population(source, hospitals, start, end, seed):
    config=m.configure(source)
    config['flag_probabilities']={k:p/4 for k,p in config['flag_probabilities'].items()}
    visits=m.generate_population(hospitals,start,end,config,seed)
    for v in visits:
        # Subsequent specialty assessment is outside this week's first-general-doctor model.
        v['requires_specialist_review']=False
    config['specialties']={k:'emergency_medicine' for k in config['specialties']}
    return visits,config


def waiting_bins(values):
    bins=[];low=-1
    for high,label in [(10,'10 minutes or less'),(24,'Over 10–24 minutes'),(60,'Over 24–60 minutes'),
                       (120,'Over 1–2 hours'),(240,'Over 2–4 hours'),(float('inf'),'Over 4 hours')]:
        count=sum(low<v<=high for v in values)
        bins.append({'label':label,'count':count,'percent':100*count/len(values)})
        low=high
    return bins


def summary_details(summary,rows):
    summary['wait_bins']=waiting_bins([w for v in rows for w in v['simulation_waits_minutes']])
    summary['stored_average_bins']=waiting_bins([v['mean_wait_to_first_doctor_minutes'] for v in rows])
    summary['bed_flag_count']=sum(v['likely_bed_occupancy'] for v in rows)
    summary['bed_flag_fraction']=summary['bed_flag_count']/len(rows)
    daily=collections.defaultdict(list)
    for v in rows:daily[v['arrival_at'][:10]].extend(v['simulation_waits_minutes'])
    summary['daily_waits']=[{'date':day,'patient_runs':len(values),**m.stats(values)} for day,values in sorted(daily.items())]
    for row in summary['daily_counts']:
        row['bed_priority_cases']=row.pop('priority_bed_cases')
        row['expected_bed_priority_cases']=row.pop('expected_priority_bed_cases')
    return summary


def export(rows,path):
    columns=['visit_id','hospital_id','arrival_at','complaint_category','likely_bed_occupancy',
             'mean_wait_to_first_doctor_minutes','mean_first_doctor_at']+[f'run_{i}_wait_minutes' for i in range(1,6)]
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for v in rows:
            row={k:v[k] for k in columns if k in v}
            row.update({f'run_{i}_wait_minutes':w for i,w in enumerate(v['simulation_waits_minutes'],1)})
            writer.writerow(row)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--seed',type=int,default=20261025)
    parser.add_argument('--days',type=int,default=30)
    args=parser.parse_args()
    if not 1 <= args.days <= 366: parser.error('--days must be between 1 and 366')
    if args.output.exists():parser.error('Use a new output directory')
    args.output.mkdir(parents=True)
    raw=args.source.read_bytes();source=json.loads(raw)
    assert source['dataset_metadata']['synthetic_data'] is True
    hospitals=[{k:h[k] for k in ('hospital_id','name','address','latitude','longitude')} for h in source['hospitals']]
    start=dt.datetime(2026,9,21,tzinfo=m.ZONE);end=start+dt.timedelta(days=args.days)
    visits,config=make_population(source,hospitals,start,end,args.seed)
    rows,snapshots,summary=m.run_scenario(visits,hospitals,start,end,config,args.seed,'constrained_month_5pct_bed_priority',
        doctor_roster=DOCTORS,triage_priority=True,bed_hold_multiplier=3)
    summary_details(summary,rows)
    serialised=[{k:value for k,value in v.items() if k not in ('requires_specialist_review','required_specialty_for_demo_model')} for v in rows]
    metadata={
        'synthetic_data':True,'model_version':'resource_queue_month_v5','seed':args.seed,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'timezone':'Europe/London',
        'warmup_start':'2026-09-18','measured_start':'2026-09-21','measured_end_exclusive':end.date().isoformat(),
        'warmup_days':3,'measured_days':args.days,'runs':5,
        'flag_semantics':'Known at reception; likely prolonged bed-supported care. Grants priority to waiting triage and waiting general-doctor queues under a demo rule; nonpreemptive. Not a clinical urgency classification.',
        'expected_flag_fraction':.05,'category_specific_flag_probabilities':config['flag_probabilities'],
        'doctors_by_four_hour_block':DOCTORS,'triage_nurses_by_four_hour_block':m.NURSES,
        'expected_arrivals_per_site_day':450,'case_mix_weighted_general_service_minutes':20,
        'general_service_cv':.6,'mean_triage_service_minutes':4.5,'triage_service_cv':.45,
        'treatment_spaces_per_site':20,'flagged_mean_bed_hold_minutes':720,'bed_hold_cv':.65,
        'endpoint':'Reception to first general-doctor contact; general-doctor service must finish before any patient leaves. Nonflagged patients leave on general assessment completion; flagged patients also wait for simulated bed-supported care to finish.',
        'shared_doctor_pool':True,'reserved_priority_doctors':0,'preemption':False,'artificial_minimum_wait':False,
        'specialty_scope':'Specialist review and transfers are not simulated or claimed available; this version models first general-doctor contact only.',
        'rounding':'Ceiling applied after averaging each patient five raw waits, integer minutes',
        'notice':'Deliberately doctor-constrained synthetic scenario, not measured hospital staffing or a validated forecast. All sites share the same assumed schedule. Bed-flag priority is a demo rule, not clinical triage guidance.',
    }
    (args.output/'queuecare_simulated_month.json').write_text(json.dumps({'dataset_metadata':metadata,'hospitals':hospitals,'visits':serialised,'staffing_snapshots':snapshots},separators=(',',':')))
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    export(rows,args.output/'patient_average_waits.csv')
    _,_,control=m.run_scenario(visits,hospitals,start,end,config,args.seed,'one_more_doctor_control',
        doctor_roster=DOCTORS,doctor_delta=1,triage_priority=True,bed_hold_multiplier=3,keep_snapshots=False)
    (args.output/'control.json').write_text(json.dumps(control,indent=2))
    measured=[v for v in visits if not v['is_warmup']]
    expected={v['visit_id']:v for v in measured}
    assert len(rows)==len(expected)
    for v in rows:
        assert v['arrival_at']==expected[v['visit_id']]['arrival_at']
        values=v['simulation_waits_minutes']
        assert len(values)==5 and all(math.isfinite(w) and w>=0 for w in values)
        assert type(v['mean_wait_to_first_doctor_minutes']) is int
        assert v['mean_wait_to_first_doctor_minutes']==math.ceil(statistics.mean(values))
    assert len(snapshots)==5*args.days*24
    (args.output/'validation.json').write_text(json.dumps({'patients':len(rows),'patient_runs':len(rows)*5,'verified_integer_averages':len(rows),
        'warmup_patients_excluded':summary['warmup_patients'],'measured_days':args.days,'hourly_snapshots':len(snapshots),'no_wait_floor':True},indent=2))
    print('Saved:',args.output,flush=True)

if __name__=='__main__':main()
