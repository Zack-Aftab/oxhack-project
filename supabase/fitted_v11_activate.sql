-- Validation precedes the active-table switch. Called inside the import transaction.
do $validate$
declare n bigint; actual bigint[];
begin
 select count(*) into n from public.demo_visit_results where dataset_id='fitted-v11';
 if n<>67676 then raise exception 'Expected 67676 imported records, got %',n; end if;
 select count(*) into n from public.demo_visit_results where dataset_id='fitted-v11' and not is_emergency;
 if n<>67473 then raise exception 'Expected 67473 hospital patients, got %',n; end if;
 select count(*) into n from public.demo_visit_results where dataset_id='fitted-v11' and is_emergency;
 if n<>203 then raise exception 'Expected 203 emergency exits, got %',n; end if;
 if abs((select avg(fitted_demo_wait_minutes) from public.demo_visit_results where dataset_id='fitted-v11' and not is_emergency)-120)>0.000001 then raise exception 'Fitted mean must be 120 minutes'; end if;
 if (select percentile_cont(.5) within group(order by fitted_demo_wait_minutes) from public.demo_visit_results where dataset_id='fitted-v11' and not is_emergency)<>100 then raise exception 'Fitted median must be 100 minutes'; end if;
 select array[count(*) filter(where fitted_demo_wait_minutes<=10),count(*) filter(where fitted_demo_wait_minutes>10 and fitted_demo_wait_minutes<=24),count(*) filter(where fitted_demo_wait_minutes>24 and fitted_demo_wait_minutes<=60),count(*) filter(where fitted_demo_wait_minutes>60 and fitted_demo_wait_minutes<=120),count(*) filter(where fitted_demo_wait_minutes>120 and fitted_demo_wait_minutes<=240),count(*) filter(where fitted_demo_wait_minutes>240)] into actual from public.demo_visit_results where dataset_id='fitted-v11' and not is_emergency;
 if actual<>array[3374,3373,15069,19425,15028,11204]::bigint[] then raise exception 'Wait distribution does not match the approved data'; end if;
 if (select count(*) from public.hospital_specialties)<>35 then raise exception 'Expected a complete 35-cell capability matrix'; end if;
 if exists(select 1 from public.demo_visit_results v cross join lateral unnest(v.complaint_categories) c join public.category_specialties cs on cs.category_id=c left join public.hospital_specialties hs on hs.hospital_id=v.hospital_id and hs.specialty_id=cs.specialty_id where v.dataset_id='fitted-v11' and not v.is_emergency and hs.supported is distinct from true) then raise exception 'A patient is assigned to an unsupported specialty'; end if;
 if (select count(*) from public.demo_capacity_hours where dataset_id='fitted-v11')<>3600 then raise exception 'Expected 3600 hourly capacity rows'; end if;
 if (select count(*) from public.demo_specialist_hours where dataset_id='fitted-v11')<>25200 then raise exception 'Expected 25200 hourly specialty staffing rows'; end if;
 if exists(select 1 from public.demo_specialist_hours s join public.hospital_specialties h using(hospital_id,specialty_id) where s.dataset_id='fitted-v11' and ((h.supported and s.doctors_on_duty<1) or (not h.supported and s.doctors_on_duty<>0))) then raise exception 'Staffing contradicts explicit capability'; end if;
end $validate$;
create schema if not exists queuecare_before_fitted_v11;
revoke all on schema queuecare_before_fitted_v11 from public,anon,authenticated;
do $backup$
declare name text; kind "char";
begin
 foreach name in array array['visits','staffing_snapshots','specialist_staffing'] loop
  select c.relkind into kind from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname=name;
  if kind in ('r','p') then
   if to_regclass('queuecare_before_fitted_v11.'||name) is not null then raise exception 'Existing backup for %; refusing to overwrite it',name; end if;
   execute format('alter table public.%I set schema queuecare_before_fitted_v11',name);
  elsif kind is not null and kind<>'v' then raise exception 'Unexpected existing object type for %',name;
  end if;
 end loop;
end $backup$;
insert into public.demo_active_dataset(singleton,dataset_id) values(true,'fitted-v11') on conflict(singleton) do update set dataset_id=excluded.dataset_id;
create or replace view public.visits with(security_invoker=true) as
select v.visit_id,v.hospital_id,v.arrival_at,v.complaint_categories[1] as complaint_category,
 v.likely_bed_occupancy,v.estimated_wait_to_first_doctor_minutes as mean_wait_to_first_doctor_minutes,
 v.arrival_at+v.estimated_wait_to_first_doctor_minutes*interval '1 minute' as mean_first_doctor_at,
 v.dataset_id,v.origin_hospital_id,v.complaint_categories,
 array(select distinct cs.specialty_id from public.category_specialties cs where cs.category_id=any(v.complaint_categories) order by cs.specialty_id) as required_specialties,
 v.pain_score,v.urgency_rating,v.manual_category_confirmation,v.raw_queue_wait_minutes,v.fitted_demo_wait_minutes,v.estimated_wait_to_first_doctor_minutes,v.wait_model,
 v.arrival_at+v.raw_queue_wait_minutes*interval '1 minute' as raw_first_doctor_at
from public.demo_visit_results v join public.demo_active_dataset active on active.dataset_id=v.dataset_id
where not v.is_emergency;
comment on view public.visits is 'Active hospital attendances. Fitted demo estimates and raw queue waits are separate. Emergency exits are retained in demo_visit_results. Previous table is privately archived.';
comment on column public.visits.mean_wait_to_first_doctor_minutes is 'Compatibility alias for ceil(fitted_demo_wait_minutes), not an average of five queue runs.';
comment on column public.visits.complaint_category is 'Compatibility projection of the first confirmed category. Use complaint_categories and complete specialist matching for recommendations.';
create or replace view public.specialist_staffing with(security_invoker=true) as
select s.hospital_id,s.specialty_id,s.shift_start,s.shift_end,s.doctors_on_duty
from public.demo_specialist_hours s join public.demo_active_dataset active on active.dataset_id=s.dataset_id;
create or replace view public.staffing_snapshots with(security_invoker=true) as
select c.dataset_id||':'||c.hospital_id||':'||extract(epoch from c.snapshot_at)::bigint::text as snapshot_id,
 c.hospital_id,c.snapshot_at,c.staffing_window_end,c.general_doctors_on_duty as general_doctors_available,
 c.triage_nurses_on_duty as triage_nurses_available,c.support_bed_capacity as beds_available,
 case when c.snapshot_at>(d.metadata->>'measured_start')::date::timestamp at time zone 'Europe/London'
 then (select count(*)::integer from public.demo_visit_results v where v.dataset_id=c.dataset_id and v.hospital_id=c.hospital_id and not v.is_emergency and v.arrival_at>=c.snapshot_at-interval '1 hour' and v.arrival_at<c.snapshot_at) else null end as observed_arrivals_last_hour,
 null::double precision as mean_general_doctors_free,null::double precision as mean_beds_free,
 null::double precision as mean_waiting_for_first_doctor,null::double precision as mean_waiting_for_triage,
 c.dataset_id,c.general_doctors_on_duty,c.triage_nurses_on_duty,c.support_bed_capacity
from public.demo_capacity_hours c join public.demo_active_dataset active on active.dataset_id=c.dataset_id
join public.simulation_datasets d on d.dataset_id=c.dataset_id;
comment on view public.staffing_snapshots is 'Active planned hourly capacity; compatibility available columns mean total on-duty/capacity. Unrecorded free-resource telemetry is NULL, not invented. Previous-hour influx is computed from arrivals; first-hour influx is unknown because warmup rows are not imported.';
create or replace view public.hospital_influx with(security_invoker=true) as
select hospital_id,(arrival_at at time zone 'Europe/London')::date as simulation_date,count(*)::integer as arrivals
from public.visits group by hospital_id,(arrival_at at time zone 'Europe/London')::date;
revoke all on public.visits,public.staffing_snapshots,public.specialist_staffing,public.hospital_influx from public,anon,authenticated;
grant select on public.visits,public.staffing_snapshots,public.specialist_staffing,public.hospital_influx to service_role;
notify pgrst,'reload schema';
