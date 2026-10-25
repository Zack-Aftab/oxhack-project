#!/usr/bin/env python3
"""One stochastic month, planned from deterministic recurring demand; no DB writes."""
import argparse,collections,csv,datetime as dt,gzip,itertools,json,math,random,statistics
from pathlib import Path
import specialists as m

ORIGIN_FACTORS={'H001':1.25,'H002':1.,'H003':.8,'H004':.9,'H005':1.05}
START=dt.datetime(2026,9,21,tzinfo=m.ZONE)
END=START+dt.timedelta(days=30)
WEEKDAY_NORM=sum(m.WEEKDAY[(START+dt.timedelta(days=i)).weekday()] for i in range(30))/30
TARGETS={'H001':105,'H002':110,'H003':120,'H004':115,'H005':140}
GENERAL_OVERHEAD=1/.85 # 15% of occupied clinician time is documentation/other duties.

def case_weights(raw,weekday,block):
 out=dict(raw)
 if weekday<5 and block==2:out['fracture_sprain_or_dislocation']*=1.8 if weekday==0 else 1.35
 if weekday in (5,6) and block in (1,2):out['abdominal_or_stomach_problems']*=1.9 if weekday==5 else 1.5
 if weekday in (4,5) and block in (0,5):
  for c in ['cuts_or_wounds','head_injury_or_neurological_symptoms']:out[c]*=1.25
 return out

def combinations(raw,weekday,block):
 weights=case_weights(raw,weekday,block);known={k:v for k,v in weights.items() if k!='unknown'};total=sum(known.values());known={k:v/total for k,v in known.items()}
 for c,p in known.items():
  yield [c],p*(1-m.MULTI_FRACTION)
  for d,q in known.items():
   if c!=d:yield [c,d],p*m.MULTI_FRACTION*q/(1-p)

def expected(source):
 raw={v['complaint_category']:v['count'] for v in source['case_mix']}
 arrivals=collections.defaultdict(float);work=collections.defaultdict(float);spec=collections.defaultdict(float)
 # One recurring week, including all possible categories and routing outcomes.
 for wd in range(7):
  for block,share in enumerate(m.SHARES):
   for cats,p in combinations(raw,wd,block):
    targets=m.eligible(cats)
    for origin,factor in ORIGIN_FACTORS.items():
     choices=[origin] if origin in targets else targets
     for h in choices:
      n=450*factor*m.WEEKDAY[wd]/WEEKDAY_NORM*share*p*(1-m.EMERGENCY_FRACTION)/len(choices)
      arrivals[h,wd,block]+=n;work[h,wd,block]+=n*max(m.WEIGHTS[c] for c in cats)
      for s in m.required(cats):spec[h,s]+=n/7
 scale=20*sum(arrivals.values())/sum(work.values())
 work={k:v*scale*GENERAL_OVERHEAD for k,v in work.items()}
 return raw,arrivals,work,spec,scale

def fluid(roster,h,work):
 # Expected flow only, no generated patient record or stochastic duration is used.
 backlog=0.;area=under=denom=0.
 for day in range(-3,30):
  wd=(START+dt.timedelta(days=day)).weekday()
  for block in range(6):
   load=work[h,wd,block]/16;capacity=roster[block]*15
   for slot in range(16):
    midpoint=max(0.,backlog+(load-capacity)/2)
    wait=midpoint/roster[block]
    if day>=0:area+=load*wait;denom+=load;under+=load*(wait<30)
    backlog=max(0.,backlog+load-capacity)
 return area/denom,under/denom,backlog

def plan(source):
 raw,arrivals,work,spec,scale=expected(source);profiles={}
 for h in m.COVERAGE:
  blockwork=[sum(work[h,w,b] for w in range(7))/7 for b in range(6)]
  roster=[max(2,round(v/240)) for v in blockwork]
  weeklywork=sum(work[h,w,b] for w in range(7) for b in range(6))
  minimum=math.ceil(weeklywork/(7*240)*1.015)
  while sum(roster)<minimum:roster[4]+=1
  def score(candidate):
   if sum(candidate)<minimum:return float('inf'),None
   mean,short,backlog=fluid(candidate,h,work)
   # Two-hour demonstration target, lower short-wait share, and no persistent instability.
   value=abs(mean-TARGETS[h])+max(0,short-.25)*100+max(0,backlog-600)/20
   return value,(mean,short,backlog)
  current,_=score(roster)
  for step in range(30):
   best=(current,roster)
   for a in range(6):
    for b in range(6):
     if a==b or roster[a]<=2:continue
     candidate=roster.copy();candidate[a]-=1;candidate[b]+=1
     value,_=score(candidate)
     if value<best[0]:best=(value,candidate)
   if best[0]>=current:break
   current,roster=best
  mean,short,backlog=fluid(roster,h,work)
  n=sum(arrivals[h,w,b] for w in range(7) for b in range(6))/7
  specialists={s:max(1,math.ceil(spec[h,s]*20/(1440*.8))) if s in m.COVERAGE[h] and s!='emergency_medicine' else 0 for s in m.SPECIALTIES}
  profiles[h]={'hospital_id':h,'supported_specialties':sorted(m.COVERAGE[h]),'support':{s:s in m.COVERAGE[h] for s in m.SPECIALTIES},'specialist_doctors_on_duty':specialists,'general_doctors_by_four_hour_block':roster,'triage_nurses_by_four_hour_block':[max(2,math.ceil(n*m.SHARES[b]*4.5/(240*.7))) for b in range(6)],'support_beds':max(8,math.ceil(n*.05*.5/.72)),'expected_daily_arrivals':n,'expected_general_doctor_utilisation':weeklywork/(7*sum(roster)*240),'fluid_planning_mean_minutes':mean,'fluid_planning_under_30_fraction':short,'fluid_end_backlog_work_minutes':backlog}
  print(h,'planned roster',roster,'expected intake',round(n),'fluid wait',round(mean,1),flush=True)
 return raw,arrivals,work,spec,scale,profiles

def population(source,seed,settings):
 raw,_,_,_,scale,profiles=settings;result=[]
 for dayno in range(-3,30):
  day=START+dt.timedelta(days=dayno);wd=day.weekday()
  shared=m.rng(seed,f'city-day:{day.date()}').lognormvariate(-.04**2/2,.04)
  for origin,factor in ORIGIN_FACTORS.items():
   local=m.rng(seed,f'local-day:{origin}:{day.date()}').lognormvariate(-.05**2/2,.05)
   for block,share in enumerate(m.SHARES):
    r=m.rng(seed,f'arrivals:{origin}:{day.date()}:{block}')
    noise=r.lognormvariate(-.04**2/2,.04)
    rate=450*factor*m.WEEKDAY[wd]/WEEKDAY_NORM*share*shared*local*noise/14400
    weights=case_weights(raw,wd,block);known={k:v for k,v in weights.items() if k!='unknown'}
    at=(day+dt.timedelta(hours=block*4)).timestamp();end=at+14400
    while True:
     at+=r.expovariate(rate)
     if at>=end:break
     vid=f'{origin}-{day.date()}-B{block}-{len(result):06}';a=m.rng(seed,f'attributes:{vid}')
     initial=a.choices(list(weights),list(weights.values()))[0];manual=initial=='unknown'
     first=a.choices(list(known),list(known.values()))[0] if manual else initial
     cats=[first]
     if a.random()<m.MULTI_FRACTION:
      other={k:v for k,v in known.items() if k!=first};cats.append(a.choices(list(other),list(other.values()))[0])
     cats=sorted(cats);flag=a.random()<.05;emergency=a.random()<m.EMERGENCY_FRACTION
     pain=min(10,max(1,round(a.triangular(1,10,3))))
     urgency=10. if flag or emergency else round(min(7.5,max(1,a.gauss(3.0+.12*(pain-3),.95))),2)
     destinations=m.eligible(cats);dest=None if emergency else origin if origin in destinations else a.choice(destinations)
     result.append({'visit_id':vid,'origin_hospital_id':origin,'hospital_id':dest,'arrival_at':m.iso(at),'initial_category':initial,'complaint_categories':cats,'manual_category_confirmation':manual,'category_confirmation_source':'synthetic_self_selection' if manual else 'synthetic_confirmation','required_specialties':m.required(cats),'likely_bed_occupancy':flag,'pain_score':pain,'urgency_rating':urgency,'queue_priority_tier':15 if flag else urgency,'is_emergency':emergency,'action':'call_999' if emergency else 'hospital_attendance','redirected_before_arrival':dest is not None and dest!=origin,'is_warmup':dayno<0})
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);p.add_argument('--seed',type=int,default=20261027);args=p.parse_args()
 if args.output.exists():p.error('Choose a new output directory')
 source=json.loads(args.source.read_text());settings=plan(source);profiles=settings[-1]
 cohort=population(source,args.seed,settings)
 # Cap urgency's queue advantage to about two minutes per point for ordinary patients.
 original_priority=m.queue_priority;m.queue_priority=lambda v:original_priority(v,aging_minutes=2)
 waits,areas,last=m.simulate(cohort,START,END,args.seed,1,settings[-2]*GENERAL_OVERHEAD,profiles)
 rows=[m.output_patient(v,[waits[v['visit_id']]] if not v['is_emergency'] else []) for v in cohort if not v['is_warmup']]
 completed=[v for v in rows if not v['is_emergency']];regular=[v for v in completed if not v['likely_bed_occupancy']];beds=[v for v in completed if v['likely_bed_occupancy']]
 values=lambda group:[v['simulation_waits_minutes'][0] for v in group]
 summary={'model_version':'demand_patterns_v8','seed':args.seed,'runs':1,'warmup_days':3,'measured_days':30,'generated_patients':len(rows),'warmup_patients':sum(v['is_warmup'] for v in cohort),'completed_hospital_patients':len(completed),'emergency_exits':sum(v['is_emergency'] for v in rows),'bed_flag_patients':sum(v['likely_bed_occupancy'] for v in rows),'individual_waits':m.stats(values(completed)),'stored_integer_waits':m.stats([v['mean_wait_to_first_doctor_minutes'] for v in completed]),'non_bed_waits':m.stats(values(regular)),'bed_waits':m.stats(values(beds)),'non_bed_over_30_percent':100*sum(w>30 for w in values(regular))/len(regular),'bed_under_20_percent':100*sum(w<20 for w in values(beds))/len(beds),'non_bed_urgency_at_least_8':sum(v['urgency_rating']>=8 for v in regular),'wait_bins':m.bins(values(completed)),'profiles':profiles,'by_hospital':[],'origin_intake':{h:sum(v['origin_hospital_id']==h for v in rows)/30 for h in profiles},'by_weekday_block':[]}
 for h in profiles:
  group=[v for v in completed if v['hospital_id']==h];z=areas[h]
  summary['by_hospital'].append({'hospital_id':h,'patients':len(group),'daily_hospital_arrivals':len(group)/30,'general_doctor_utilisation':z['general_busy_seconds']/z['general_capacity_seconds'],'bed_utilisation':z['bed_busy_seconds']/z['bed_capacity_seconds'],**m.stats(values(group))})
 for wd in range(7):
  for block in range(6):
   group=[v for v in completed if (t:=dt.datetime.fromisoformat(v['arrival_at'])).weekday()==wd and t.hour//4==block]
   summary['by_weekday_block'].append({'weekday':wd,'four_hour_block':block,'patients':len(group),'category_counts':dict(collections.Counter(c for v in group for c in v['complaint_categories'])),**m.stats(values(group))})
 metadata={'synthetic_data':True,'model_version':'demand_patterns_v8','measured_start':START.date().isoformat(),'measured_end_exclusive':END.date().isoformat(),'runs':1,'warmup_days':3,'seed':args.seed,'origin_daily_targets':{h:450*f for h,f in ORIGIN_FACTORS.items()},'day_multipliers':m.WEEKDAY,'four_hour_arrival_shares':m.SHARES,'patterns':'Invented Monday 08–12 fracture x1.8; other weekday 08–12 x1.35; Saturday 04–12 abdominal x1.9; Sunday x1.5; Friday/Saturday late and early head/wounds x1.25. No causal evidence about bikes or alcohol.','randomness':'Poisson within-block arrivals, shared-city daily 4%, local daily 5%, block 4% mean-one lognormal factors; lognormal service durations.','priority':'Bed class 15 ahead of ordinary; stored bed urgency remains 10. Ordinary urgency truncated normal mean about 3, max7.5; queue aging one point per2min. Nonpreemptive.','planning':'Deterministic expected weekly case-work and eligibility routing; integer rosters locally calibrated toward 105–140min fluid waits with >=1.5% weekly capacity reserve. This is target calibration, not NHS validation; only one stochastic month is run.','general_service':'20min case-mix mean direct work +15% of occupied time for documentation/other duties; total mean23.53min.','bed_support':'5% independent synthetic bed need; mean12h hold; capacity planned at72% nominal occupancy.','distribution':'No sampled wait floor or forced normal waiting-time distribution. Waits emerge from queues.','live_database_changed':False}
 args.output.mkdir(parents=True);dataset={'dataset_metadata':metadata,'hospitals':source['hospitals'],'hospital_specialties':profiles,'visits':rows}
 (args.output/'dataset.json.gz').write_bytes(gzip.compress(json.dumps(dataset,separators=(',',':')).encode(),mtime=0));(args.output/'summary.json').write_text(json.dumps(summary,indent=2));(args.output/'metadata.json').write_text(json.dumps(metadata,indent=2))
 for v in completed:
  assert v['hospital_id'] in m.eligible(v['complaint_categories']) and len(v['simulation_waits_minutes'])==1
  assert v['mean_wait_to_first_doctor_minutes']==math.ceil(v['simulation_waits_minutes'][0])
  assert 1<=v['urgency_rating']<=10 and (not v['likely_bed_occupancy'] or v['urgency_rating']==10 and v['queue_priority_tier']==15)
 with (args.output/'patient_results.csv').open('w',newline='') as f:
  cols=['visit_id','origin_hospital_id','hospital_id','arrival_at','complaint_categories','pain_score','urgency_rating','queue_priority_tier','likely_bed_occupancy','is_emergency','mean_wait_to_first_doctor_minutes','raw_wait_minutes'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
  for v in rows:w.writerow({**{k:json.dumps(v[k]) if k=='complaint_categories' else v[k] for k in cols if k in v},'raw_wait_minutes':v['simulation_waits_minutes'][0] if v['simulation_waits_minutes'] else None})
 print(json.dumps({k:summary[k] for k in ['generated_patients','individual_waits','non_bed_waits','bed_waits','non_bed_over_30_percent','bed_under_20_percent']},indent=2),flush=True)
if __name__=='__main__':main()
