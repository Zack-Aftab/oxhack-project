#!/usr/bin/env python3
"""Explicit fitted demo waits; raw event-queue results remain separate and unchanged."""
import argparse,bisect,csv,gzip,json,math,statistics
from pathlib import Path
import specialists as m

def percentile_rank(value,source):
 if not math.isfinite(value) or value<0:raise ValueError('Queue wait must be finite and nonnegative')
 left=bisect.bisect_left(source,value);right=bisect.bisect_right(source,value);n=len(source)
 if right>left:return (left+right)/(2*n)
 if left==0:return max(0.,.5/n*value/source[0]) if source[0]>0 else .5/n
 if left==n:raise ValueError('Raw queue wait exceeds calibration support; retain the raw result instead')
 fraction=(value-source[left-1])/(source[left]-source[left-1])
 return (left-.5+fraction)/n

def quantile_parts(u,model):
 cuts=model['cumulative_probabilities'];bounds=[0.,10.,24.,60.,120.,240.]
 band=next((i for i,high in enumerate(cuts) if u<=high),5)
 low=cuts[band-1] if band else 0.;high=cuts[band]
 t=max(0.,min(1.-1e-15,(u-low)/(high-low)))
 if band==5:return 240.,-math.log1p(-t)
 power=model['middle_power'] if band==3 else model['two_to_four_hour_power'] if band==4 else 1.
 return bounds[band]+(bounds[band+1]-bounds[band])*t**power,0.

def apply_fitted_wait(queue_wait,model):
 u=percentile_rank(queue_wait,model['source_queue_waits_sorted'])
 base,tail=quantile_parts(u,model)
 return round(base+model['tail_scale_minutes']*tail,10)

def fit_model(queue_waits,target,mean=120.,median=100.):
 if len(target)!=6 or any(not math.isfinite(p) or p<=0 for p in target) or abs(sum(target)-100)>1e-7:raise ValueError('Six positive percentages must sum to 100')
 if not 60<median<120:raise ValueError('This fitted median must lie inside the 60–120 minute band')
 source=sorted(queue_waits)
 if not source or any(not math.isfinite(w) or w<0 for w in source):raise ValueError('Invalid source waits')
 cuts=[];total=0.
 for p in target:total+=p/100;cuts.append(total)
 cuts[-1]=1.
 if not cuts[2]<.5<cuts[3]:raise ValueError('Target median must be in the fourth band')
 t=(.5-cuts[2])/(cuts[3]-cuts[2]);power=math.log((median-60)/60)/math.log(t)
 model={'model_version':'fitted_demo_v11','target_percentages':target,'cumulative_probabilities':cuts,'target_mean_minutes':mean,'target_median_minutes':median,'middle_power':power,'two_to_four_hour_power':2.,'source_queue_waits_sorted':source,'outside_training_support':'Raw values above the training maximum are rejected; retain the raw queue result. Not a validated extrapolator.','refit_on_capacity_change':False}
 parts=[quantile_parts(percentile_rank(w,source),model) for w in source]
 base=statistics.mean(p[0] for p in parts);tail=statistics.mean(p[1] for p in parts)
 scale=(mean-base)/tail
 if scale<=0 or not math.isfinite(scale):raise ValueError('Requested mean is incompatible with the other targets')
 model['tail_scale_minutes']=scale
 return model

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source_results',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
 if args.output.exists():p.error('Choose a new output directory')
 data=json.loads(gzip.decompress((args.source_results/'dataset.json.gz').read_bytes()));source_summary=json.loads((args.source_results/'summary.json').read_text())
 queue=[v['simulation_waits_minutes'][0] for v in data['visits'] if not v['is_emergency']]
 targets=source_summary['target_percentages'];model=fit_model(queue,targets)
 rows=[]
 for v in data['visits']:
  row={k:value for k,value in v.items() if k not in ['simulation_waits_minutes','simulation_run_count','mean_wait_to_first_doctor_minutes','mean_first_doctor_at']}
  raw=v['simulation_waits_minutes'][0] if not v['is_emergency'] else None
  fitted=apply_fitted_wait(raw,model) if raw is not None else None
  row.update(raw_queue_wait_minutes=raw,fitted_demo_wait_minutes=fitted,estimated_wait_to_first_doctor_minutes=math.ceil(fitted) if fitted is not None else None,wait_model='fitted_demo_v11')
  rows.append(row)
 completed=[v for v in rows if not v['is_emergency']];waits=[v['fitted_demo_wait_minutes'] for v in completed]
 summary={'model_version':'fitted_demo_v11','synthetic_data':True,'waiting_time_method':'Explicit statistical fit of the user-approved demo distribution, not raw queue waiting time.','generated_patients':len(rows),'hospital_patients':len(completed),'emergency_exits':len(rows)-len(completed),'source_queue_statistics':m.stats(queue),'fitted_wait_statistics':m.stats(waits),'stored_integer_wait_statistics':m.stats([v['estimated_wait_to_first_doctor_minutes'] for v in completed]),'target_percentages':targets,'wait_bins':m.bins(waits),'by_hospital':[],'bed_waits':m.stats([v['fitted_demo_wait_minutes'] for v in completed if v['likely_bed_occupancy']]),'non_bed_waits':m.stats([v['fitted_demo_wait_minutes'] for v in completed if not v['likely_bed_occupancy']]),'live_database_changed':False}
 for h in data['hospital_specialties']:
  group=[v['fitted_demo_wait_minutes'] for v in completed if v['hospital_id']==h];summary['by_hospital'].append({'hospital_id':h,**m.stats(group)})
 metadata={'model_version':'fitted_demo_v11','synthetic_data':True,'user_approved_method':'Fit the synthetic wait distribution to my targets.','notice':'Designer distribution for a demo, not a clinical prediction or validated NHS statistic. Raw queue waits are retained separately.','source_model_version':data['dataset_metadata']['model_version'],'measured_start':data['dataset_metadata']['measured_start'],'measured_end_exclusive':data['dataset_metadata']['measured_end_exclusive'],'warmup_days':3,'source_simulation_runs':1,'target_percentages':targets,'target_mean_minutes':120,'target_median_minutes':100,'method':'One shared monotone empirical-CDF-to-quantile mapping across all sites; preserves queue-derived ordering and ties. Power-shaped within-band quantiles, exponential tail; tail scale fitted to mean120; fourth-band power fitted to median100. Integer stored estimate is ceil(fitted wait).','capacity_use':'Queue rankings already include doctor rosters, beds, urgency, staffing, specialties and recurring/random intake. Hold this fitted mapping fixed when evaluating different raw queue outcomes; automatic refitting would erase changes to the overall distribution.','limitations':'Fitted to one synthetic month. Per-site distributions are not independently forced. Raw queue values above the fitted support are rejected so severe overload cannot silently be capped. Does not reproduce treatment-resource event timings. No validated causal or clinical interpretation.','live_database_changed':False}
 args.output.mkdir(parents=True)
 for name,obj in [('summary.json',summary),('metadata.json',metadata)]: (args.output/name).write_text(json.dumps(obj,indent=2))
 for name,obj in [('model.json.gz',model),('dataset.json.gz',{'dataset_metadata':metadata,'hospital_specialties':data['hospital_specialties'],'visits':rows})]: (args.output/name).write_bytes(gzip.compress(json.dumps(obj,separators=(',',':')).encode(),mtime=0))
 with (args.output/'patient_results.csv').open('w',newline='') as f:
  cols=['visit_id','origin_hospital_id','hospital_id','arrival_at','complaint_categories','pain_score','urgency_rating','likely_bed_occupancy','is_emergency','raw_queue_wait_minutes','fitted_demo_wait_minutes','estimated_wait_to_first_doctor_minutes','wait_model'];writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
  for v in rows:writer.writerow({k:json.dumps(v[k]) if k=='complaint_categories' else v[k] for k in cols})
 assert abs(summary['fitted_wait_statistics']['mean']-120)<1e-6 and abs(summary['fitted_wait_statistics']['median']-100)<1e-6
 print(json.dumps({'statistics':summary['fitted_wait_statistics'],'integer_statistics':summary['stored_integer_wait_statistics'],'bins':summary['wait_bins'],'bed':summary['bed_waits']},indent=2))
if __name__=='__main__':main()
