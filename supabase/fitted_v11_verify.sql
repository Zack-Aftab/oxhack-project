select dataset_id from public.demo_active_dataset;
select count(*) as hospital_patients,round(avg(fitted_demo_wait_minutes)::numeric,2) as fitted_mean_minutes,percentile_cont(.5) within group(order by fitted_demo_wait_minutes) as fitted_median_minutes,round(avg(mean_wait_to_first_doctor_minutes)::numeric,2) as stored_integer_mean_minutes from public.visits;
select count(*) as emergency_exits from public.demo_visit_results where dataset_id='fitted-v11' and is_emergency;
select label,count(*) as patients,round(100.*count(*)/sum(count(*)) over(),2) as percentage from (select case when fitted_demo_wait_minutes<=10 then '1. <=10 minutes' when fitted_demo_wait_minutes<=24 then '2. >10-24 minutes' when fitted_demo_wait_minutes<=60 then '3. >24-60 minutes' when fitted_demo_wait_minutes<=120 then '4. >1-2 hours' when fitted_demo_wait_minutes<=240 then '5. >2-4 hours' else '6. >4 hours' end as label from public.visits) grouped group by label order by label;
select count(*) as explicit_capability_cells from public.hospital_specialties;
select count(*) as hourly_hospital_capacity_rows from public.staffing_snapshots;
select count(*) as hourly_specialist_staffing_rows from public.specialist_staffing;
