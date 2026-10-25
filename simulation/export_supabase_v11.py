#!/usr/bin/env python3
"""Build a self-contained SQL Editor import. No network, secrets or live mutations."""
import argparse,csv,collections,datetime as dt,gzip,hashlib,json,math,statistics,zipfile
from pathlib import Path
import specialists as m
ROOT=Path(__file__).resolve().parents[1]

def literal(v):return "'"+str(v).replace("'","''")+"'"
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);args=p.parse_args()
 if args.output.exists():p.error('Choose a new output directory')
 args.output.mkdir(parents=True)
 data=json.loads(gzip.decompress((ROOT/'simulation/results/fitted-v11/dataset.json.gz').read_bytes()));summary=json.loads((ROOT/'simulation/results/fitted-v11/summary.json').read_text());model=json.loads(gzip.decompress((ROOT/'simulation/results/fitted-v11/model.json.gz').read_bytes()));profiles=data['hospital_specialties'];rows=data['visits'];cats=list(m.MAPPING);known=[c for c in cats if c!='unknown'];epoch=dt.datetime(1970,1,1,tzinfo=dt.timezone.utc)
 meta={**data['dataset_metadata'],'timezone':'Europe/London','notice':'Explicitly fitted synthetic demo waits, not observed or validated clinical waiting times. Raw event-queue waits are stored separately. Specialty coverage and staffing are invented.','category_specific_flag_probabilities':{c:.05 for c in cats},'comparison_estimates':{},'fitted_model_parameters':{k:v for k,v in model.items() if k!='source_queue_waits_sorted'},'fitted_model_sha256':hashlib.sha256((ROOT/'simulation/results/fitted-v11/model.json.gz').read_bytes()).hexdigest(),'fitted_model_artifact':'https://github.com/Zack-Aftab/oxhack-project/blob/5f5bfef/simulation/results/fitted-v11/model.json.gz','source_queue_runs':1}
 for h in profiles:
  group=[v for v in rows if v['hospital_id']==h and not v['is_emergency']];bands={}
  for band in range(1,11):
   values=[v['fitted_demo_wait_minutes'] for v in group if math.floor(v['urgency_rating'])==band]
   if values:bands[str(band)]={'mean':statistics.mean(values),'count':len(values)}
  meta['comparison_estimates'][h]={'bands':bands,'pooled':{'mean':statistics.mean(v['fitted_demo_wait_minutes'] for v in group),'count':len(group)}}
 sql=["-- QueueCare fitted-v11: apply to the existing project in Supabase SQL Editor.\n-- Public synthetic data only. Entire import, validation, backup and activation are transactional.\nbegin;\nselect pg_advisory_xact_lock(hashtext('queuecare-fitted-v11'));\nset local statement_timeout='300s';",(ROOT/'supabase/migrations/202610250003_fitted_demo_prepare.sql').read_text()]
 for s in m.SPECIALTIES:sql.append(f'insert into public.specialties values({literal(s)},{literal(s.replace("_"," ").title())}) on conflict(specialty_id) do update set label=excluded.label;')
 for c,s in m.MAPPING.items():sql.append(f'insert into public.category_specialties values({literal(c)},{literal(s)},{str(c=="unknown").lower()}) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;')
 for h,p in profiles.items():
  for s,value in p['support'].items():sql.append(f'insert into public.hospital_specialties values({literal(h)},{literal(s)},{str(value).lower()}) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;')
 sql.append("insert into public.simulation_datasets(dataset_id,model_version,metadata,summary) values('fitted-v11','fitted_demo_v11',$meta$"+json.dumps(meta,separators=(',',':'))+"$meta$::jsonb,$summary$"+json.dumps(summary,separators=(',',':'))+"$summary$::jsonb) on conflict(dataset_id) do update set model_version=excluded.model_version,metadata=excluded.metadata,summary=excluded.summary;")
 sql.append("delete from public.demo_fitted_v11_import;\ndelete from public.demo_capacity_hours where dataset_id='fitted-v11';\ndelete from public.demo_specialist_hours where dataset_id='fitted-v11';")
 profile_json=json.dumps(profiles,separators=(',',':'))
 capacity_sql="""with profiles as(select key hospital_id,value p from jsonb_each($profiles$"""+profile_json+"""$profiles$::jsonb)), slots as(select t snapshot_at from generate_series(timestamptz '2026-09-21 00:00:00+01',timestamptz '2026-10-20 23:00:00+01',interval '1 hour') t), schedule as(select hospital_id,p,snapshot_at,extract(hour from snapshot_at at time zone 'Europe/London')::integer h from profiles cross join slots)
insert into public.demo_capacity_hours select 'fitted-v11',hospital_id,snapshot_at,snapshot_at+interval '1 hour',case when p?'general_doctors_by_hour' then (p->'general_doctors_by_hour'->>h)::integer else (p->'general_doctors_by_four_hour_block'->>(h/4))::integer end,(p->'triage_nurses_by_four_hour_block'->>(h/4))::integer,(p->>'support_beds')::integer from schedule;
with profiles as(select key hospital_id,value p from jsonb_each($profiles$"""+profile_json+"""$profiles$::jsonb))
insert into public.demo_specialist_hours select c.dataset_id,c.hospital_id,s.key,c.snapshot_at,c.staffing_window_end,case when s.key='emergency_medicine' then c.general_doctors_on_duty else s.value::text::integer end from public.demo_capacity_hours c join profiles p using(hospital_id) cross join lateral jsonb_each(p.p->'specialist_doctors_on_duty') s where c.dataset_id='fitted-v11';"""
 sql.append(capacity_sql)
 prepare='\n'.join(sql)
 wire=[];csv_rows=[]
 for v in rows:
  at=dt.datetime.fromisoformat(v['arrival_at']);delta=at.astimezone(dt.timezone.utc)-epoch;micros=delta.days*86400000000+delta.seconds*1000000+delta.microseconds
  sequence=int(v['visit_id'].rsplit('-',1)[1]);reconstructed=f"{v['origin_hospital_id']}-{at.date()}-B{at.hour//4}-{sequence:06}"
  assert reconstructed==v['visit_id']
  mask=sum(1<<known.index(c) for c in v['complaint_categories']);flags=int(v['likely_bed_occupancy'])+2*int(v['is_emergency'])+4*int(v['manual_category_confirmation'])
  fields=[int(v['origin_hospital_id'][1:]),int(v['hospital_id'][1:]) if v['hospital_id'] else 0,micros,sequence,mask,cats.index(v['initial_category']),v['pain_score'],v['urgency_rating'],flags,v['raw_queue_wait_minutes'],v['fitted_demo_wait_minutes'],v['estimated_wait_to_first_doctor_minutes']]
  csv_rows.append(fields);wire.append('\t'.join('' if x is None else str(x) for x in fields))
 payload="with raw as(select string_to_array(line,E'\\t') f from regexp_split_to_table($visits$"+'\n'.join(wire)+"$visits$,E'\\n') line) insert into public.demo_fitted_v11_import select f[1]::smallint,f[2]::smallint,f[3]::bigint,f[4]::integer,f[5]::integer,f[6]::smallint,f[7]::smallint,f[8]::double precision,f[9]::smallint,nullif(f[10],'')::double precision,nullif(f[11],'')::double precision,nullif(f[12],'')::integer from raw;"
 catarray='array['+','.join(literal(c) for c in known)+']::text[]';initialarray='array['+','.join(literal(c) for c in cats)+']::text[]'
 decode="""do $wire_check$ begin if (select count(*) from public.demo_fitted_v11_import)<>67676 then raise exception 'Import all 67676 CSV rows before activation'; end if; end $wire_check$;
delete from public.demo_visit_results where dataset_id='fitted-v11';
with decoded as(select *,timestamptz '1970-01-01 00:00:00+00'+(arrival_epoch_microseconds/1000000)*interval '1 second'+(arrival_epoch_microseconds%1000000)*interval '1 microsecond' as arrival from public.demo_fitted_v11_import)
insert into public.demo_visit_results select 'fitted-v11','H'||lpad(origin_code::text,3,'0')||'-'||to_char(arrival at time zone 'Europe/London','YYYY-MM-DD')||'-B'||floor(extract(hour from arrival at time zone 'Europe/London')/4)::text||'-'||lpad(visit_sequence::text,6,'0'),'H'||lpad(origin_code::text,3,'0'),case when destination_code=0 then null else 'H'||lpad(destination_code::text,3,'0') end,arrival,("""+initialarray+""")[initial_category_index+1],array(select c from unnest("""+catarray+""") with ordinality categories(c,i) where (category_mask & (1 << (i::integer-1)))<>0),(flags & 1)<>0,pain_score,urgency_rating,(flags & 2)<>0,(flags & 4)<>0,raw_queue_wait_minutes,fitted_demo_wait_minutes,estimated_wait_to_first_doctor_minutes,'fitted_demo_v11' from decoded;
"""
 activation=decode+(ROOT/'supabase/fitted_v11_activate.sql').read_text()
 verify=(ROOT/'supabase/fitted_v11_verify.sql').read_text()
 final=prepare+'\n'+payload+'\n'+activation+'\ncommit;\n'+verify
 (args.output/'APPLY_FITTED_V11.sql').write_text(final)
 (args.output/'VERIFY.sql').write_text(verify)
 (args.output/'01_PREPARE_FALLBACK.sql').write_text(prepare+'\ncommit;\n')
 (args.output/'03_ACTIVATE_FALLBACK.sql').write_text("begin;\nselect pg_advisory_xact_lock(hashtext('queuecare-fitted-v11'));\nset local statement_timeout='300s';\n"+activation+'\ncommit;\n'+verify)
 with (args.output/'02_IMPORT_ROWS.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['origin_code','destination_code','arrival_epoch_microseconds','visit_sequence','category_mask','initial_category_index','pain_score','urgency_rating','flags','raw_queue_wait_minutes','fitted_demo_wait_minutes','estimated_wait_to_first_doctor_minutes']);w.writerows(csv_rows)
 (args.output/'README.txt').write_text('Recommended: open APPLY_FITTED_V11.sql as text, copy all contents into a new SQL query at https://supabase.com/dashboard/project/wlxljcobmhjmvnhjlvlk/sql/new and click Run. The complete import, backup and activation are transactional. Do not rerun older migrations 001/003.\n\nIf SQL Editor rejects the size, use this smaller three-step fallback instead:\n1. Run 01_PREPARE_FALLBACK.sql in SQL Editor.\n2. In Table Editor select demo_fitted_v11_import, choose Import data from CSV, and import 02_IMPORT_ROWS.csv (67676 rows). It contains only scalar columns; empty wait cells mean NULL.\n3. Run 03_ACTIVATE_FALLBACK.sql in SQL Editor. It refuses activation unless every row and all statistics validate.\n\nVERIFY.sql checks the result. Old public visits/staffing tables are preserved in the private queuecare_before_fitted_v11 schema. Existing month-v5 metadata remains archived by its original dataset ID. Active public visits becomes a view over fitted results; raw waits remain a separate column. Emergency exits live in demo_visit_results. No key is needed in chat. Synthetic demo only. The app server should use SUPABASE_DATASET_ID=fitted-v11 and SUPABASE_MULTI_DATASET_ID=fitted-v11.\n')
 zip_path=ROOT/'downloads/supabase-fitted-v11.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
  for file in args.output.iterdir():z.write(file,file.name)
 print('Prepared SQL import:',len(rows),'visits, 3600 capacity hours, 25200 specialty hours;',len(final.encode()),'SQL bytes')
if __name__=='__main__':main()
