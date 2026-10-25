#!/usr/bin/env python3
"""Synthetic specialist eligibility + continuous urgency simulation. No database writes."""
import argparse
import bisect
import collections
import datetime as dt
import gzip
import hashlib
import heapq
import itertools
import json
import math
import random
import statistics
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE=ZoneInfo('Europe/London')
MAPPING={
 'fracture_sprain_or_dislocation':'orthopaedics',
 'cuts_or_wounds':'wound_care_or_plastics',
 'head_injury_or_neurological_symptoms':'neurology_or_neurosurgery',
 'breathing_problems':'respiratory_medicine',
 'chest_pain_or_heart_symptoms':'cardiology',
 'abdominal_or_stomach_problems':'general_surgery_or_gastroenterology',
 'other_or_uncategorised':'emergency_medicine',
 'unknown':'emergency_medicine', # Display mapping only: unknown is NEVER eligible.
}
SPECIALTIES=sorted(set(MAPPING.values()))
COVERAGE={
 'H001':set(SPECIALTIES),
 'H002':{'orthopaedics','wound_care_or_plastics','respiratory_medicine','emergency_medicine'},
 'H003':{'respiratory_medicine','cardiology','emergency_medicine'},
 'H004':{'wound_care_or_plastics','cardiology','general_surgery_or_gastroenterology','emergency_medicine'},
 'H005':{'orthopaedics','neurology_or_neurosurgery','general_surgery_or_gastroenterology','emergency_medicine'},
}
DOCTORS=[3,3,8,10,9,6]
NURSES=[2,2,3,3,3,2]
SHARES=[.08,.06,.20,.24,.26,.16]
WEEKDAY=[.99,1,1,1,1.04,1.02,.95]
WEIGHTS={k:v for k,v in zip(MAPPING,[20,15,25,25,30,25,15,20])}
FLAG_WEIGHTS={k:v for k,v in zip(MAPPING,[.22,.12,.30,.30,.35,.18,.10,.10])}
EMERGENCY_FRACTION=.003
MULTI_FRACTION=.20

def rng(seed,key):return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{key}'.encode()).digest()[:16],'big'))
def stamp(t):return dt.datetime.fromisoformat(t).timestamp()
def iso(t):return dt.datetime.fromtimestamp(t,ZONE).isoformat()
def duration(r,mean,cv=.6):
 s=math.sqrt(math.log1p(cv*cv));return r.lognormvariate(math.log(mean)-s*s/2,s)*60

def required(categories):
 if not categories or 'unknown' in categories or any(c not in MAPPING for c in categories):raise ValueError('Self-categorisation required')
 return sorted({MAPPING[c] for c in categories})

def eligible(categories):
 needs=set(required(categories))
 return [h for h,coverage in COVERAGE.items() if needs<=coverage]

def quantile(a,q):
 a=sorted(a);i=(len(a)-1)*q;lo=math.floor(i);hi=math.ceil(i);return a[lo]+(a[hi]-a[lo])*(i-lo)

def stats(a):
 return {'count':len(a),'mean':statistics.mean(a),'median':statistics.median(a),'p90':quantile(a,.9),'p95':quantile(a,.95),'max':max(a)} if a else None

def bins(a):
 result=[];low=-1
 for high,label in [(10,'10 minutes or less'),(24,'Over 10–24 minutes'),(60,'Over 24–60 minutes'),(120,'Over 1–2 hours'),(240,'Over 2–4 hours'),(float('inf'),'Over 4 hours')]:
  n=sum(low<w<=high for w in a);result.append({'label':label,'count':n,'percent':100*n/len(a)});low=high
 return result

def plan(source):
 raw={r['complaint_category']:r['count'] for r in source['case_mix']};total=sum(raw.values())
 known={c:n/(total-raw['unknown']) for c,n in raw.items() if c!='unknown'}
 flag_mean=sum(raw[c]/total*FLAG_WEIGHTS[c] for c in raw)
 combinations=[]
 for first,p in known.items():
  combinations.append(([first],p*(1-MULTI_FRACTION)))
  for second,q in known.items():
   if first!=second:combinations.append(([first,second],p*MULTI_FRACTION*q/(1-p)))
 # Plan staffing from the GENERATIVE distribution, not realised future arrivals.
 workload=collections.Counter();general_work=collections.Counter();specialist_work=collections.Counter()
 mean_work=sum(p*max(WEIGHTS[c] for c in cats) for cats,p in combinations)
 service_scale=20/mean_work
 for cats,p in combinations:
  targets=eligible(cats)
  for origin in COVERAGE:
   destinations=[origin] if origin in targets else targets
   for h in destinations:
    arrivals=2250*(1-EMERGENCY_FRACTION)*p/5/len(destinations)
    workload[h]+=arrivals;general_work[h]+=arrivals*max(WEIGHTS[c] for c in cats)*service_scale
    for specialty in required(cats):specialist_work[h,specialty]+=arrivals
 profiles={}
 for h in COVERAGE:
  ratio=workload[h]/450
  doctors=[max(2,math.floor(n*ratio+.5)) for n in DOCTORS]
  while sum(doctors)*240 < general_work[h]/.985:doctors[4]+=1
  specialists={s:(max(1,math.ceil(specialist_work[h,s]*20/(1440*.80))) if s in COVERAGE[h] and s!='emergency_medicine' else 0) for s in SPECIALTIES}
  profiles[h]={'hospital_id':h,'supported_specialties':sorted(COVERAGE[h]),'support':{s:s in COVERAGE[h] for s in SPECIALTIES},
   'specialist_doctors_on_duty':specialists,'general_doctors_by_four_hour_block':doctors,
   'triage_nurses_by_four_hour_block':[max(2,math.ceil(n*ratio)) for n in NURSES],
   'support_beds':max(8,math.ceil(20*ratio)), 'expected_daily_arrivals':workload[h],
   'expected_general_doctor_utilisation':general_work[h]/(sum(doctors)*240)}
 return raw,known,flag_mean,service_scale,profiles

def population(source,start,end,seed,settings):
 raw,known,flag_mean,service_scale,profiles=settings
 categories=list(raw);weights=list(raw.values());known_ids=list(known);known_weights=list(known.values())
 result=[];day=start-dt.timedelta(days=3)
 while day<end:
  for hospital in source['hospitals']:
   origin=hospital['hospital_id'];daily_rng=rng(seed,f'day:{origin}:{day.date()}')
   s=math.sqrt(math.log1p(.08**2));daily=daily_rng.lognormvariate(-s*s/2,s)
   for block,share in enumerate(SHARES):
    r=rng(seed,f'arrivals:{origin}:{day.date()}:{block}');begin=(day+dt.timedelta(hours=block*4)).timestamp();at=begin
    while True:
     at+=r.expovariate(450*WEEKDAY[day.weekday()]*daily*share/14400)
     if at>=begin+14400:break
     initial=r.choices(categories,weights,k=1)[0];vid=f'{origin}-{day.date()}-B{block}-{len(result):06}'
     labels=rng(seed,f'attributes:{vid}')
     manual=initial=='unknown'
     first=labels.choices(known_ids,known_weights,k=1)[0] if manual else initial
     confirmed=[first]
     if labels.random()<MULTI_FRACTION:
      options=[c for c in known_ids if c!=first];confirmed.append(labels.choices(options,[known[c] for c in options],k=1)[0])
     confirmed=sorted(confirmed)
     flag=labels.random()<.05*FLAG_WEIGHTS[initial]/flag_mean
     pain=min(10,max(1,math.ceil(1+9*labels.betavariate(1.8,3))))
     emergency=labels.random()<EMERGENCY_FRACTION
     context=.15*(block in (0,1,5))+.10*(day.weekday()>=5)
     score=round(min(9.99,max(1,1+9*(.25*((pain-1)/9)+.75*labels.betavariate(2,3))+context)),2)
     if flag or emergency:score=10.0
     destinations=eligible(confirmed)
     destination=None if emergency else origin if origin in destinations else labels.choice(destinations)
     result.append({'visit_id':vid,'origin_hospital_id':origin,'hospital_id':destination,'arrival_at':iso(at),
      'initial_category':initial,'complaint_categories':confirmed,'manual_category_confirmation':manual,
      'category_confirmation_source':'synthetic_self_selection' if manual else 'synthetic_confirmation',
      'required_specialties':required(confirmed),'likely_bed_occupancy':flag,'pain_score':pain,'urgency_rating':score,
      'is_emergency':emergency,'action':'call_999' if emergency else 'hospital_attendance',
      'redirected_before_arrival':destination is not None and destination!=origin,'is_warmup':day<start})
  day+=dt.timedelta(days=1)
 return result

def simulate(visits,start,end,seed,run,service_scale,profiles):
 patients=[v for v in visits if not v['is_emergency']]
 events=[];serial=0
 def push(at,kind,value,h):
  nonlocal serial
  order=1 if kind=='shift' else 2 if kind=='arrival' else 0
  heapq.heappush(events,(at,order,serial,kind,value,h));serial+=1
 for i,v in enumerate(patients):push(stamp(v['arrival_at']),'arrival',i,v['hospital_id'])
 t=start-dt.timedelta(days=3)
 while t<end+dt.timedelta(days=30):
  for h in profiles:push(t.timestamp(),'shift',t.hour//4,h)
  t+=dt.timedelta(hours=4)
 queues={h:{'triage':[],'general':[],'specialist':collections.defaultdict(list)} for h in profiles}
 busy={h:{'triage':0,'general':0,'beds':0,'specialist':collections.Counter()} for h in profiles}
 caps={};last={h:(start-dt.timedelta(days=3)).timestamp() for h in profiles};integrals={h:collections.Counter() for h in profiles}
 first={};finished={};triaged={};general_done=set();hold_done=set();special_done=set();spec_index=collections.Counter();work={}
 for i,v in enumerate(patients):
  r=rng(seed,f'work:{run}:{v["visit_id"]}')
  work[i]={'triage':duration(r,4.5,.45),'general':duration(r,max(WEIGHTS[c] for c in v['complaint_categories'])*service_scale),
           'specialist':{s:duration(r,20,.5) for s in v['required_specialties'] if s!='emergency_medicine'},
           'hold':duration(r,720,.65) if v['likely_bed_occupancy'] else 0}
 def priority(i):
  v=patients[i];return (-v['urgency_rating'],stamp(v['arrival_at']),v['visit_id'],i)
 def advance(h,now):
  elapsed=max(0,min(now,end.timestamp())-max(last[h],start.timestamp()))
  if h in caps:
   z=integrals[h];b=busy[h];p=profiles[h]
   z['general_busy_seconds']+=elapsed*b['general'];z['general_capacity_seconds']+=elapsed*p['general_doctors_by_four_hour_block'][caps[h]]
   z['bed_busy_seconds']+=elapsed*b['beds'];z['bed_capacity_seconds']+=elapsed*p['support_beds']
   z['specialist_busy_seconds']+=elapsed*sum(b['specialist'].values());z['specialist_capacity_seconds']+=elapsed*sum(p['specialist_doctors_on_duty'].values())
  last[h]=now
 def release(i,now,h):
  if i not in finished and i in general_done and i in hold_done and i in special_done:
   busy[h]['beds']-=int(patients[i]['likely_bed_occupancy']);finished[i]=now
 def next_specialist(i,now,h):
  choices=[s for s in patients[i]['required_specialties'] if s!='emergency_medicine']
  if spec_index[i]==len(choices):special_done.add(i);release(i,now,h)
  else:heapq.heappush(queues[h]['specialist'][choices[spec_index[i]]],priority(i))
 while events:
  now,_,_,kind,value,h=heapq.heappop(events);advance(h,now)
  q=queues[h];b=busy[h];profile=profiles[h]
  if kind=='shift':caps[h]=value
  elif kind=='arrival':heapq.heappush(q['triage'],priority(value))
  elif kind=='triaged':
   b['triage']-=1;triaged[value]=now;heapq.heappush(q['general'],priority(value))
  elif kind=='general_done':
   b['general']-=1;general_done.add(value);next_specialist(value,now,h);release(value,now,h)
  elif kind=='specialist_done':
   i,s=value;b['specialist'][s]-=1;spec_index[i]+=1;next_specialist(i,now,h)
  elif kind=='hold_done':hold_done.add(value);release(value,now,h)
  if h not in caps:continue
  block=caps[h]
  while q['triage'] and b['triage']<profile['triage_nurses_by_four_hour_block'][block]:
   i=heapq.heappop(q['triage'])[-1];b['triage']+=1;push(now+work[i]['triage'],'triaged',i,h)
  for s,line in q['specialist'].items():
   while line and b['specialist'][s]<profile['specialist_doctors_on_duty'][s]:
    i=heapq.heappop(line)[-1];b['specialist'][s]+=1;push(now+work[i]['specialist'][s],'specialist_done',(i,s),h)
  blocked=[]
  while q['general'] and b['general']<profile['general_doctors_by_four_hour_block'][block]:
   item=heapq.heappop(q['general']);i=item[-1];v=patients[i]
   if v['likely_bed_occupancy'] and b['beds']>=profile['support_beds']:blocked.append(item);continue
   b['general']+=1;b['beds']+=int(v['likely_bed_occupancy']);first[i]=now
   push(now+work[i]['general'],'general_done',i,h)
   if v['likely_bed_occupancy']:push(now+work[i]['hold'],'hold_done',i,h)
   else:hold_done.add(i)
  for item in blocked:heapq.heappush(q['general'],item)
  assert min(b['general'],b['triage'],b['beds'])>=0 and b['beds']<=profile['support_beds']
  if len(finished)==len(patients) and now>=end.timestamp():break
 for h in profiles:advance(h,max(last[h],end.timestamp()))
 assert len(first)==len(finished)==len(patients),'Unserved patients: impossible staffing/capability configuration'
 waits={}
 for i,v in enumerate(patients):
  assert stamp(v['arrival_at'])<=triaged[i]<=first[i]<=finished[i]
  assert set(v['required_specialties'])<=COVERAGE[v['hospital_id']]
  if not v['is_warmup']:waits[v['visit_id']]=(first[i]-stamp(v['arrival_at']))/60
 return waits,integrals,max(finished.values())

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--seed',type=int,default=20261026)
 args=parser.parse_args()
 if args.output.exists():parser.error('Choose a new output directory')
 args.output.mkdir(parents=True)
 source=json.loads(args.source.read_text());start=dt.datetime(2026,9,21,tzinfo=ZONE);end=start+dt.timedelta(days=30)
 settings=plan(source);raw,known,flag_mean,scale,profiles=settings
 cohort=population(source,start,end,args.seed,settings);samples=collections.defaultdict(list);run_stats=[];total_integrals={h:collections.Counter() for h in profiles}
 for run in range(1,6):
  waits,areas,last=simulate(cohort,start,end,args.seed,run,scale,profiles)
  for vid,value in waits.items():samples[vid].append(value)
  for h,v in areas.items():total_integrals[h].update(v)
  run_stats.append({'run':run,**stats(list(waits.values())),'last_completion_at':iso(last)})
  print(f'Run {run}/5: {len(waits)} completed non-emergency visits, mean {statistics.mean(waits.values()):.2f}, median {statistics.median(waits.values()):.2f}',flush=True)
 rows=[]
 for v in cohort:
  if v['is_warmup']:continue
  values=samples.get(v['visit_id'],[]);mean=math.ceil(statistics.mean(values)) if values else None
  rows.append({k:val for k,val in v.items() if k!='is_warmup'} | {'simulation_waits_minutes':values,'simulation_run_count':len(values),
   'mean_wait_to_first_doctor_minutes':mean,'mean_first_doctor_at':iso(stamp(v['arrival_at'])+mean*60) if mean is not None else None})
 completed=[v for v in rows if not v['is_emergency']];all_waits=[w for v in completed for w in v['simulation_waits_minutes']]
 summary={'model_version':'specialist_urgency_v6','measured_days':30,'warmup_days':3,'runs':5,'generated_patients':len(rows),
 'warmup_patients':sum(v['is_warmup'] for v in cohort),'completed_hospital_patients':len(completed),'emergency_exits':sum(v['is_emergency'] for v in rows),
 'patient_runs':len(completed)*5,'manual_self_categorisations':sum(v['manual_category_confirmation'] for v in rows),
 'multiple_category_patients':sum(len(v['complaint_categories'])>1 for v in rows),
 'bed_flag_patients':sum(v['likely_bed_occupancy'] for v in rows),'redirected_before_arrival':sum(v['redirected_before_arrival'] for v in rows),
 'individual_waits':stats(all_waits),'stored_integer_averages':stats([v['mean_wait_to_first_doctor_minutes'] for v in completed]),'wait_bins':bins(all_waits),
 'urgency':stats([v['urgency_rating'] for v in rows]),'run_stats':run_stats,'profiles':profiles,'by_hospital':[],'by_urgency':[]}
 for h,p in profiles.items():
  group=[v for v in completed if v['hospital_id']==h];z=total_integrals[h]
  summary['by_hospital'].append({'hospital_id':h,'patients':len(group),'general_doctor_utilisation':z['general_busy_seconds']/z['general_capacity_seconds'],
  'bed_utilisation':z['bed_busy_seconds']/z['bed_capacity_seconds'],'specialist_utilisation':z['specialist_busy_seconds']/z['specialist_capacity_seconds'],
  **stats([w for v in group for w in v['simulation_waits_minutes']])})
 for low,high in [(1,3),(3,6),(6,9.99),(9.99,10)]:
  group=[v for v in completed if (v['urgency_rating']>=low if low==1 else v['urgency_rating']>low) and v['urgency_rating']<=high]
  summary['by_urgency'].append({'range':[low,high],'patients':len(group),'waits':stats([w for v in group for w in v['simulation_waits_minutes']])})
 metadata={'synthetic_data':True,'model_version':'specialist_urgency_v6','seed':args.seed,'measured_start':start.date().isoformat(),'measured_end_exclusive':end.date().isoformat(),
 'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'category_mapping':MAPPING,'profile_source':'invented demo capability and staffing profiles, not verified hospital facts',
 'urgency_source':'synthetic patient attributes, not Gemini inference or clinical triage','bed_flag_implies_urgency':10.0,
 'expected_bed_fraction':.05,'expected_emergency_fraction':EMERGENCY_FRACTION,'expected_multi_category_fraction':MULTI_FRACTION,
 'self_category_rule':'Unknown requires a fictional explicit self-selection before any recommendation; unsupported unknown requests are rejected by matching.',
 'staffing_rule':'Analytical expected routing distribution, rounded base roster, minimum nominal general-doctor capacity at 98.5% expected load; no realised future arrivals used.',
 'routing_rule':'Retain origin if it covers all confirmed categories; otherwise seeded uniform choice among eligible sites BEFORE arrival. This is not a live travel/wait-optimal redirection policy.',
 'service_means':{'general':20,'triage':4.5,'each_specialist_review':20,'flagged_bed_hold':720},
 'queue_rule':'Highest floating urgency first at triage, general and specialist queues; FCFS tie-break, nonpreemptive. General contact occurs before all required specialist reviews.',
 'limits':'No true clinical assessment, real travel, ambulance pathway, inpatient system, patient abandonment or operating response to overcrowding. One hub supports every modelled specialty, not every medical specialty.'}
 dataset={'dataset_metadata':metadata,'hospitals':source['hospitals'],'hospital_specialties':profiles,'visits':rows}
 payload=json.dumps(dataset,separators=(',',':')).encode();(args.output/'dataset.json.gz').write_bytes(gzip.compress(payload,mtime=0))
 (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
 # Basic full-output integrity, not just a zero-test or syntax check.
 assert len(rows)==len(completed)+summary['emergency_exits']
 for v in rows:
  assert 1<=v['urgency_rating']<=10 and (not v['likely_bed_occupancy'] or v['urgency_rating']==10)
  if v['is_emergency']:assert v['hospital_id'] is None and v['mean_wait_to_first_doctor_minutes'] is None
  else:
   assert v['hospital_id'] in eligible(v['complaint_categories'])
   assert len(v['simulation_waits_minutes'])==5 and all(math.isfinite(w) and w>=0 for w in v['simulation_waits_minutes'])
   assert type(v['mean_wait_to_first_doctor_minutes']) is int and v['mean_wait_to_first_doctor_minutes']==math.ceil(statistics.mean(v['simulation_waits_minutes']))
 (args.output/'validation.json').write_text(json.dumps({'patients_checked':len(rows),'counts_reconcile':True,'all_completed_patients_specialty_matched':True,'all_bed_flags_max_urgency':True,'every_completed_patient_has_five_samples_and_integer_mean':True,'explicit_boolean_coverage_cells':len(profiles)*len(SPECIALTIES),'hub_covers_all_known_combinations':True},indent=2))
 print('Saved',args.output,flush=True)

if __name__=='__main__':main()
