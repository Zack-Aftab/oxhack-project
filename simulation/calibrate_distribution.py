#!/usr/bin/env python3
"""Calibrate synthetic staffing to requested wait bands; never rewrite patient waits."""
import argparse,collections,copy,csv,gzip,json,math,multiprocessing,statistics,time
from pathlib import Path
import demand_patterns as d
m=d.m
SEED=20261027
LOSS_WEIGHTS=[4,2,1,1,1,1]

def percentages(waits):return [x['percent'] for x in m.bins(waits)]
def loss(actual,target):return sum(w*(a-b)**2 for w,a,b in zip(LOSS_WEIGHTS,actual,target))

def fluid_bands(roster,h,work,arrivals):
 backlog=0.;counts=[0.]*6
 for day in range(-3,30):
  wd=(d.START+d.dt.timedelta(days=day)).weekday()
  for block in range(len(roster)):
   original=block//4 if len(roster)==24 else block
   slots=4 if len(roster)==24 else 16
   load=work[h,wd,original]/16;capacity=roster[block]*15;n=arrivals[h,wd,original]/16
   for slot in range(slots):
    wait=max(0,backlog+(load-capacity)/2)/roster[block]
    if day>=0:
     index=next((i for i,bound in enumerate([10,24,60,120,240]) if wait<=bound),5);counts[index]+=n
    backlog=max(0,backlog+load-capacity)
 total=sum(counts)
 return [100*n/total for n in counts]

def worker(job):
 h,patients,profile,old_roster,work,arrivals,scale,target,rounds,folder,resume,hourly=job
 original=m.queue_priority;m.queue_priority=lambda v:original(v,aging_minutes=2)
 trials=[];cache={};best=None
 if resume:
  for trial in json.loads(Path(resume,f'{h}-trials.json').read_text()):
   if trial['beds']<profile['support_beds'] or len(trial['roster'])!=(24 if hourly else 6):continue
   trial=dict(trial);trial['loss']=loss(trial['percentages'],target);trial['trial']=len(trials);trials.append(trial);cache[tuple(trial['roster']),trial['beds']]=trial
   if best is None or trial['loss']<best['loss']:best=trial
 def evaluate(roster,beds):
  nonlocal best
  key=(tuple(roster),beds)
  if key in cache:return cache[key]
  p=copy.deepcopy(profile);p['general_doctors_by_hour' if hourly else 'general_doctors_by_four_hour_block']=list(roster);p['support_beds']=beds
  waits,areas,last=m.simulate(patients,d.START,d.END,SEED,1,scale*d.GENERAL_OVERHEAD,{h:p})
  actual=percentages(list(waits.values()));value=loss(actual,target)
  trial={'hospital_id':h,'trial':len(trials),'roster':list(roster),'beds':beds,'percentages':actual,'loss':value,'mean':statistics.mean(waits.values()),'median':statistics.median(waits.values())}
  cache[key]=trial;trials.append(trial)
  if best is None or value<best['loss']:
   best=trial;print(h,'trial',trial['trial'],'best loss',round(value,1),'bins',[round(x,1) for x in actual],flush=True)
  return trial
 if hourly:
  for initial in [profile['general_doctors_by_four_hour_block'],old_roster]:
   evaluate([n for n in initial for _ in range(4)],profile['support_beds'])
 else:
  evaluate(profile['general_doctors_by_four_hour_block'],profile['support_beds'])
  evaluate(old_roster,profile['support_beds'])
 capacity_work=sum(work[h,w,b] for w in range(7) for b in range(6))/7
 daily=[sum(work[h,w,b] for w in range(7))/7/240 for b in range(6)]
 for lag in ([0,.2,.4] if hourly else [0,.1,.2,.3,.4,.5,.65]):
  expected=[(1-lag)*daily[b]+lag*daily[(b-1)%6] for b in range(6)]
  for reserve in [1.005,1.02]:
   count=max(sum(max(2,math.floor(n)) for n in expected),math.ceil(capacity_work/240*reserve))
   roster=[max(2,math.floor(n)) for n in expected]
   while sum(roster)<count:
    b=max(range(6),key=lambda i:expected[i]-roster[i]);roster[b]+=1
   if hourly:
    for stagger in [0,.5]:
     smooth=[(1-((hour%4+.5)/4))*roster[(hour//4-1)%6]+((hour%4+.5)/4)*roster[hour//4] for hour in range(24)] if stagger else [n for n in roster for _ in range(4)]
     hourly_roster=[max(2,math.floor(n)) for n in smooth]
     while sum(hourly_roster)<sum(roster)*4:
      b=max(range(24),key=lambda i:smooth[i]-hourly_roster[i]);hourly_roster[b]+=1
     evaluate(hourly_roster,profile['support_beds'])
   else:evaluate(roster,profile['support_beds'])
 r=m.rng(SEED,f'calibrate:{h}')
 for step in range(rounds):
  current=best;roster=current['roster'];currentfluid=fluid_bands(roster,h,work,arrivals);candidates=[]
  for a in range(len(roster)):
   for b in range(-1,len(roster)):
    if a==b or roster[a]<=2 or hourly and b>=0 and min(abs(a-b),24-abs(a-b))>4:continue
    cand=roster.copy();cand[a]-=1
    if b>=0:cand[b]+=1
    # Preserve adequate aggregate capacity, allow shifting/removing previously added doctor-hours.
    if sum(cand)*(60 if hourly else 240)<capacity_work*1.005:continue
    key=(tuple(cand),current['beds'])
    if key in cache:continue
    future=fluid_bands(cand,h,work,arrivals)
    estimate=[max(0,act+new-old) for act,new,old in zip(current['percentages'],future,currentfluid)]
    total=sum(estimate);estimate=[100*x/total for x in estimate]
    candidates.append((loss(estimate,target),cand,current['beds']))
  # Bed headroom remains realistic; it is not used to delay ordinary cases artificially.
  for beds in {max(profile['support_beds'],current['beds']-1),current['beds']+1}:
   if (tuple(roster),beds) not in cache:candidates.append((current['loss']+5,list(roster),beds))
  if not candidates:break
  candidates.sort(key=lambda x:x[0]);chosen=candidates[0]
  if step%8==7 and len(candidates)>3:chosen=candidates[r.randrange(min(5,len(candidates)))]
  evaluate(chosen[1],chosen[2])
  if best['loss']<30:break
 Path(folder,f'{h}-trials.json').write_text(json.dumps(trials,indent=2))
 return best,trials

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--rounds',type=int,default=24);p.add_argument('--resume-from',type=Path);p.add_argument('--hourly',action='store_true');p.add_argument('--short-wait-weight',type=float,default=4);p.add_argument('--trials-from',type=Path,nargs='+');args=p.parse_args()
 LOSS_WEIGHTS[0]=args.short_wait_weight
 if args.output.exists():p.error('Choose a new output folder')
 args.output.mkdir(parents=True)
 source=json.loads(args.source.read_text());settings=d.plan(source);raw,arrivals,work,spec,scale,profiles=settings
 old=copy.deepcopy(profiles);d.adjust_capacity(profiles,1,.65,8);cohort=d.population(source,SEED,settings)
 previous=json.loads((Path(__file__).parent/'results/capacity-v9/summary.json').read_text())
 tail=[x['percent'] for x in previous['wait_bins'][2:]];target=[5.,5.]+[90*x/sum(tail) for x in tail]
 jobs=[(h,[v for v in cohort if v['hospital_id']==h],profiles[h],old[h]['general_doctors_by_four_hour_block'],work,arrivals,scale,target,args.rounds,str(args.output),str(args.resume_from) if args.resume_from else None,args.hourly) for h in profiles]
 if args.trials_from:
  results=[]
  for h in profiles:
   unique={}
   for directory in args.trials_from:
    for record in json.loads((directory/f'{h}-trials.json').read_text()):
     if record['beds']<profiles[h]['support_beds']:continue
     record=dict(record);record['loss']=loss(record['percentages'],target)
     unique[tuple(record['roster']),record['beds']]=record
   trials=list(unique.values());results.append((min(trials,key=lambda x:x['loss']),trials))
   (args.output/f'{h}-trials.json').write_text(json.dumps(trials,indent=2))
 else:
  with multiprocessing.Pool(min(5,len(jobs))) as pool:results=pool.map(worker,jobs)
 # Choose the combination of each site's top candidates nearest the aggregate target.
 groups=[sorted(trials,key=lambda x:x['loss'])[:8] for _,trials in results];counts=[sum(not v['is_warmup'] and not v['is_emergency'] and v['hospital_id']==h for v in cohort) for h in profiles];total=sum(counts)
 import itertools
 combinations=[]
 for combination in itertools.product(*groups):
  aggregate=[sum(n*x['percentages'][i] for n,x in zip(counts,combination))/total for i in range(6)]
  combinations.append((loss(aggregate,target),combination,aggregate))
 value,chosen,expected=min(combinations,key=lambda x:x[0]);original=m.queue_priority;m.queue_priority=lambda v:original(v,aging_minutes=2)
 for h,selected in zip(profiles,chosen):
  profile=profiles[h];profile['general_doctors_by_hour' if len(selected['roster'])==24 else 'general_doctors_by_four_hour_block']=selected['roster'];profile['support_beds']=selected['beds']
  base=old[h]['general_doctors_by_four_hour_block'];profile['expected_general_doctor_utilisation']=old[h]['expected_general_doctor_utilisation']*sum(base)*(4 if len(selected['roster'])==24 else 1)/sum(selected['roster'])
 waits,areas,last=m.simulate(cohort,d.START,d.END,SEED,1,scale*d.GENERAL_OVERHEAD,profiles)
 rows=[m.output_patient(v,[waits[v['visit_id']]] if not v['is_emergency'] else []) for v in cohort if not v['is_warmup']]
 completed=[v for v in rows if not v['is_emergency']];allwaits=list(waits.values());summary={'model_version':'distribution_capacity_v10','seed':SEED,'runs_per_capacity_configuration':1,'warmup_days':3,'measured_days':30,'generated_patients':len(rows),'completed_hospital_patients':len(completed),'emergency_exits':sum(v['is_emergency'] for v in rows),'target_percentages':target,'wait_bins':m.bins(allwaits),'individual_waits':m.stats(allwaits),'calibration_loss':value,'trial_counts':{h:len(trials) for h,(_,trials) in zip(profiles,results)},'profiles':profiles,'by_hospital':[]}
 assert all(abs(a-b)<1e-7 for a,b in zip(percentages(allwaits),expected))
 for h in profiles:
  group=[v for v in completed if v['hospital_id']==h];samples=[v['simulation_waits_minutes'][0] for v in group];z=areas[h]
  summary['by_hospital'].append({'hospital_id':h,'patients':len(group),'wait_bins':m.bins(samples),'general_doctor_utilisation':z['general_busy_seconds']/z['general_capacity_seconds'],'bed_utilisation':z['bed_busy_seconds']/z['bed_capacity_seconds'],**m.stats(samples)})
 metadata={'synthetic_data':True,'model_version':'distribution_capacity_v10','seed':SEED,'measured_start':d.START.date().isoformat(),'measured_end_exclusive':d.END.date().isoformat(),'warmup_days':3,'measured_days':30,'target_percentages':target,'target_source':'User-requested 5% at <=10, 5% over10 to24, remaining90% proportional to v9 longer-wait bands. Not measured hospital statistics.','calibration':'Integer general roster and bed search against one fixed synthetic month; all trial results disclosed. Future demand and other seeds may differ. Same cohort, durations, categories, triage/specialists, priorities and flags as v8/v9.','waiting_time_generation':'Unmodified event-queue simulation; no post-hoc wait editing, rejection sampling, forced minimum, or patient reassignment.','live_database_changed':False}
 (args.output/'dataset.json.gz').write_bytes(gzip.compress(json.dumps({'dataset_metadata':metadata,'hospitals':source['hospitals'],'hospital_specialties':profiles,'visits':rows},separators=(',',':')).encode(),mtime=0))
 for name,obj in [('summary.json',summary),('metadata.json',metadata)]: (args.output/name).write_text(json.dumps(obj,indent=2))
 with (args.output/'patient_results.csv').open('w',newline='') as f:
  cols=['visit_id','origin_hospital_id','hospital_id','arrival_at','complaint_categories','pain_score','urgency_rating','queue_priority_tier','likely_bed_occupancy','is_emergency','mean_wait_to_first_doctor_minutes','raw_wait_minutes'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for v in rows:w.writerow({**{k:json.dumps(v[k]) if k=='complaint_categories' else v[k] for k in cols if k in v},'raw_wait_minutes':v['simulation_waits_minutes'][0] if v['simulation_waits_minutes'] else None})
 print('FINAL',json.dumps({'targets':target,'actual':percentages(allwaits),'stats':summary['individual_waits'],'trial_counts':summary['trial_counts']}),flush=True)
if __name__=='__main__':main()
