#!/usr/bin/env python3
"""Export selected v7 results, CSV, API metadata and additive seed SQL."""
import argparse,csv,datetime as dt,gzip,importlib.util,json,math,statistics
from pathlib import Path
spec=importlib.util.spec_from_file_location('model',Path(__file__).with_name('specialists.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('results',type=Path);args=p.parse_args();folder=args.results
 data=json.loads(gzip.decompress((folder/'dataset.json.gz').read_bytes()));summary=json.loads((folder/'summary.json').read_text());profiles=data['hospital_specialties']
 estimates={}
 for h in profiles:
  rows=[v for v in data['visits'] if v['hospital_id']==h and not v['is_emergency']]
  bands={}
  for band in range(1,11):
   cohort=[v for v in rows if math.floor(v['urgency_rating'])==band]
   if cohort:bands[str(band)]={'mean':statistics.mean(w for v in cohort for w in v['simulation_waits_minutes']),'count':len(cohort)}
  estimates[h]={'bands':bands,'pooled':{'mean':statistics.mean(w for v in rows for w in v['simulation_waits_minutes']),'count':len(rows)}}
 metadata={**data['dataset_metadata'],'notice':'Synthetic demo. All category-specialist links, coverage, staffing, urgency, travel and waits are invented; hospital names are not evidence of actual service availability.', 'comparison_estimates':estimates}
 (folder/'api-metadata.json').write_text(json.dumps(metadata,indent=2))
 with (folder/'patient_results.csv').open('w',newline='') as f:
  cols=['visit_id','origin_hospital_id','hospital_id','arrival_at','complaint_categories','required_specialties','manual_category_confirmation','pain_score','urgency_rating','likely_bed_occupancy','is_emergency','mean_wait_to_first_doctor_minutes']+[f'run_{i}_wait_minutes' for i in range(1,6)]
  writer=csv.DictWriter(f,fieldnames=cols);writer.writeheader()
  for v in data['visits']:
   row={k:v[k] for k in cols if k in v}
   for key in ['complaint_categories','required_specialties']:row[key]=json.dumps(row[key])
   row.update({f'run_{i}_wait_minutes':w for i,w in enumerate(v['simulation_waits_minutes'],1)})
   writer.writerow(row)
 labels={'orthopaedics':'Orthopaedics','wound_care_or_plastics':'Wound care / plastics','neurology_or_neurosurgery':'Neurology / neurosurgery','respiratory_medicine':'Respiratory medicine','cardiology':'Cardiology','general_surgery_or_gastroenterology':'General surgery / gastroenterology','emergency_medicine':'General / emergency medicine'}
 sql=['-- Hypothetical profiles. Run after the additive specialist_catalog migration.','-- Does not replace existing visits, staffing snapshots or the month-v5 metadata row.','begin;']
 def literal(x):return "'"+str(x).replace("'","''")+"'"
 for key,value in labels.items():sql.append(f'insert into public.specialties values({literal(key)},{literal(value)}) on conflict(specialty_id) do update set label=excluded.label;')
 for category,specialty in m.MAPPING.items():sql.append(f'insert into public.category_specialties values({literal(category)},{literal(specialty)},{str(category=="unknown").lower()}) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;')
 for h,profile in profiles.items():
  for specialty in m.SPECIALTIES:sql.append(f'insert into public.hospital_specialties values({literal(h)},{literal(specialty)},{str(profile["support"][specialty]).lower()}) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;')
 start=dt.datetime.fromisoformat(metadata['measured_start']).replace(tzinfo=m.ZONE);end=dt.datetime.fromisoformat(metadata['measured_end_exclusive']).replace(tzinfo=m.ZONE)
 values=[];t=start
 while t<end:
  for h,profile in profiles.items():
   for specialty in m.SPECIALTIES:
    count=profile['general_doctors_by_four_hour_block'][t.hour//4] if specialty=='emergency_medicine' else profile['specialist_doctors_on_duty'][specialty]
    values.append(f'({literal(h)},{literal(specialty)},{literal(t.isoformat())},{literal((t+dt.timedelta(hours=4)).isoformat())},{count})')
  t+=dt.timedelta(hours=4)
 sql.append('insert into public.specialist_staffing(hospital_id,specialty_id,shift_start,shift_end,doctors_on_duty) values\n'+',\n'.join(values)+'\non conflict(hospital_id,specialty_id,shift_start) do update set shift_end=excluded.shift_end,doctors_on_duty=excluded.doctors_on_duty;')
 light_summary={k:summary[k] for k in ['model_version','generated_patients','completed_hospital_patients','emergency_exits','individual_waits','stored_integer_averages']}
 sql.append('insert into public.simulation_datasets(dataset_id,model_version,metadata,summary) values (\'specialist-v7\',\'specialist_urgency_v7\',$queuecare_meta$'+json.dumps(metadata)+'$queuecare_meta$::jsonb,$queuecare_summary$'+json.dumps(light_summary)+'$queuecare_summary$::jsonb) on conflict(dataset_id) do update set model_version=excluded.model_version,metadata=excluded.metadata,summary=excluded.summary;')
 sql+=['notify pgrst,\'reload schema\';','commit;']
 (folder/'seed.sql').write_text('\n'.join(sql)+'\n')
 print('Exported CSV, API metadata and seed SQL:',len(values),'staffing windows')
if __name__=='__main__':main()
