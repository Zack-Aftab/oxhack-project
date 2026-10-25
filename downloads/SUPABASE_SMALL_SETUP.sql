-- QueueCare fitted-v11: apply to the existing project in Supabase SQL Editor.
-- Public synthetic data only. Entire import, validation, backup and activation are transactional.
begin;
select pg_advisory_xact_lock(hashtext('queuecare-fitted-v11'));
set local statement_timeout='300s';
-- Preparation only. Use the generated APPLY_FITTED_V11.sql for the complete atomic import.
-- No existing visits or staffing are replaced by this preparation file.
create table if not exists public.specialties(specialty_id text primary key,label text not null);
create table if not exists public.category_specialties(category_id text primary key,specialty_id text not null references public.specialties,requires_manual_selection boolean not null default false);
create table if not exists public.hospital_specialties(hospital_id text not null references public.hospitals,specialty_id text not null references public.specialties,supported boolean not null,primary key(hospital_id,specialty_id));
create table if not exists public.demo_visit_results(
 dataset_id text not null references public.simulation_datasets,
 visit_id text not null,
 origin_hospital_id text not null references public.hospitals,
 hospital_id text references public.hospitals,
 arrival_at timestamptz not null,
 initial_category text not null references public.category_specialties,
 complaint_categories text[] not null,
 likely_bed_occupancy boolean not null,
 pain_score smallint not null check(pain_score between 1 and 10),
 urgency_rating double precision not null check(urgency_rating between 1 and 10),
 is_emergency boolean not null,
 manual_category_confirmation boolean not null,
 raw_queue_wait_minutes double precision,
 fitted_demo_wait_minutes double precision,
 estimated_wait_to_first_doctor_minutes integer,
 wait_model text not null check(wait_model='fitted_demo_v11'),
 primary key(dataset_id,visit_id),
 check(not likely_bed_occupancy or urgency_rating=10),
 check(cardinality(complaint_categories) between 0 and 7 and array_position(complaint_categories,null) is null),
 check(not ('unknown'=any(complaint_categories))),
 check(complaint_categories <@ array['fracture_sprain_or_dislocation','cuts_or_wounds','head_injury_or_neurological_symptoms','breathing_problems','chest_pain_or_heart_symptoms','abdominal_or_stomach_problems','other_or_uncategorised']::text[]),
 check((is_emergency and urgency_rating=10 and hospital_id is null and cardinality(complaint_categories)=0 and raw_queue_wait_minutes is null and fitted_demo_wait_minutes is null and estimated_wait_to_first_doctor_minutes is null)
    or (not is_emergency and hospital_id is not null and cardinality(complaint_categories)>0 and raw_queue_wait_minutes is not null and fitted_demo_wait_minutes is not null and estimated_wait_to_first_doctor_minutes is not null)),
 check(raw_queue_wait_minutes>=0 and raw_queue_wait_minutes<'Infinity'::double precision),
 check(fitted_demo_wait_minutes>=0 and fitted_demo_wait_minutes<'Infinity'::double precision),
 check(estimated_wait_to_first_doctor_minutes=ceil(fitted_demo_wait_minutes))
);
create index if not exists demo_visit_hospital_time_idx on public.demo_visit_results(dataset_id,hospital_id,arrival_at);
create table if not exists public.demo_capacity_hours(
 dataset_id text not null references public.simulation_datasets,
 hospital_id text not null references public.hospitals,
 snapshot_at timestamptz not null,
 staffing_window_end timestamptz not null,
 general_doctors_on_duty integer not null check(general_doctors_on_duty>0),
 triage_nurses_on_duty integer not null check(triage_nurses_on_duty>0),
 support_bed_capacity integer not null check(support_bed_capacity>0),
 primary key(dataset_id,hospital_id,snapshot_at),
 check(staffing_window_end=snapshot_at+interval '1 hour')
);
create table if not exists public.demo_specialist_hours(
 dataset_id text not null references public.simulation_datasets,
 hospital_id text not null,
 specialty_id text not null,
 shift_start timestamptz not null,
 shift_end timestamptz not null,
 doctors_on_duty integer not null check(doctors_on_duty>=0),
 primary key(dataset_id,hospital_id,specialty_id,shift_start),
 foreign key(hospital_id,specialty_id) references public.hospital_specialties,
 check(shift_end=shift_start+interval '1 hour')
);
create index if not exists demo_specialist_window_idx on public.demo_specialist_hours(dataset_id,shift_start,shift_end);
create table if not exists public.demo_active_dataset(singleton boolean primary key default true check(singleton),dataset_id text not null references public.simulation_datasets);
comment on table public.demo_visit_results is 'Synthetic fitted demo estimates and separate raw event-queue waits. Emergency exits have no hospital wait. No real clinical data.';
comment on column public.demo_visit_results.estimated_wait_to_first_doctor_minutes is 'Integer ceiling of the user-approved fitted demo estimate, not the raw queue wait or a five-run average.';
comment on table public.demo_capacity_hours is 'Planned on-duty staffing and total support-bed capacity, not live idle doctors/free beds.';
alter table public.specialties enable row level security;
alter table public.category_specialties enable row level security;
alter table public.hospital_specialties enable row level security;
alter table public.demo_visit_results enable row level security;
alter table public.demo_capacity_hours enable row level security;
alter table public.demo_specialist_hours enable row level security;
alter table public.demo_active_dataset enable row level security;
revoke all on public.specialties,public.category_specialties,public.hospital_specialties,public.demo_visit_results,public.demo_capacity_hours,public.demo_specialist_hours,public.demo_active_dataset from public,anon,authenticated;
grant select,insert,update,delete on public.specialties,public.category_specialties,public.hospital_specialties,public.demo_visit_results,public.demo_capacity_hours,public.demo_specialist_hours,public.demo_active_dataset to service_role;
create table if not exists public.demo_fitted_v11_import(
 origin_code smallint not null check(origin_code between 1 and 5),
 destination_code smallint not null check(destination_code between 0 and 5),
 arrival_epoch_microseconds bigint not null,
 visit_sequence integer primary key,
 category_mask integer not null,
 initial_category_index smallint not null,
 pain_score smallint not null,
 urgency_rating double precision not null,
 flags smallint not null,
 raw_queue_wait_minutes double precision,
 fitted_demo_wait_minutes double precision,
 estimated_wait_to_first_doctor_minutes integer
);
alter table public.demo_fitted_v11_import enable row level security;
revoke all on public.demo_fitted_v11_import from public,anon,authenticated;
grant select,insert,update,delete on public.demo_fitted_v11_import to service_role;

insert into public.specialties values('cardiology','Cardiology') on conflict(specialty_id) do update set label=excluded.label;
insert into public.specialties values('emergency_medicine','Emergency Medicine') on conflict(specialty_id) do update set label=excluded.label;
insert into public.specialties values('general_surgery_or_gastroenterology','General Surgery Or Gastroenterology') on conflict(specialty_id) do update set label=excluded.label;
insert into public.specialties values('neurology_or_neurosurgery','Neurology Or Neurosurgery') on conflict(specialty_id) do update set label=excluded.label;
insert into public.specialties values('orthopaedics','Orthopaedics') on conflict(specialty_id) do update set label=excluded.label;
insert into public.specialties values('respiratory_medicine','Respiratory Medicine') on conflict(specialty_id) do update set label=excluded.label;
insert into public.specialties values('wound_care_or_plastics','Wound Care Or Plastics') on conflict(specialty_id) do update set label=excluded.label;
insert into public.category_specialties values('fracture_sprain_or_dislocation','orthopaedics',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('cuts_or_wounds','wound_care_or_plastics',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('head_injury_or_neurological_symptoms','neurology_or_neurosurgery',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('breathing_problems','respiratory_medicine',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('chest_pain_or_heart_symptoms','cardiology',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('abdominal_or_stomach_problems','general_surgery_or_gastroenterology',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('other_or_uncategorised','emergency_medicine',false) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.category_specialties values('unknown','emergency_medicine',true) on conflict(category_id) do update set specialty_id=excluded.specialty_id,requires_manual_selection=excluded.requires_manual_selection;
insert into public.hospital_specialties values('H001','cardiology',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H001','emergency_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H001','general_surgery_or_gastroenterology',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H001','neurology_or_neurosurgery',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H001','orthopaedics',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H001','respiratory_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H001','wound_care_or_plastics',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','cardiology',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','emergency_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','general_surgery_or_gastroenterology',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','neurology_or_neurosurgery',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','orthopaedics',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','respiratory_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H002','wound_care_or_plastics',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','cardiology',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','emergency_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','general_surgery_or_gastroenterology',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','neurology_or_neurosurgery',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','orthopaedics',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','respiratory_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H003','wound_care_or_plastics',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','cardiology',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','emergency_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','general_surgery_or_gastroenterology',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','neurology_or_neurosurgery',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','orthopaedics',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','respiratory_medicine',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H004','wound_care_or_plastics',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','cardiology',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','emergency_medicine',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','general_surgery_or_gastroenterology',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','neurology_or_neurosurgery',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','orthopaedics',true) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','respiratory_medicine',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.hospital_specialties values('H005','wound_care_or_plastics',false) on conflict(hospital_id,specialty_id) do update set supported=excluded.supported;
insert into public.simulation_datasets(dataset_id,model_version,metadata,summary) values('fitted-v11','fitted_demo_v11',$meta${"model_version":"fitted_demo_v11","synthetic_data":true,"user_approved_method":"Fit the synthetic wait distribution to my targets.","notice":"Explicitly fitted synthetic demo waits, not observed or validated clinical waiting times. Raw event-queue waits are stored separately. Specialty coverage and staffing are invented.","source_model_version":"distribution_capacity_v10","measured_start":"2026-09-21","measured_end_exclusive":"2026-10-21","warmup_days":3,"source_simulation_runs":1,"target_percentages":[5.0,5.0,22.333169472778668,28.788865675310316,22.27233624185818,16.605628610052847],"target_mean_minutes":120,"target_median_minutes":100,"method":"One shared monotone empirical-CDF-to-quantile mapping across all sites; preserves queue-derived ordering and ties. Power-shaped within-band quantiles, exponential tail; tail scale fitted to mean120; fourth-band power fitted to median100. Integer stored estimate is ceil(fitted wait).","capacity_use":"Queue rankings already include doctor rosters, beds, urgency, staffing, specialties and recurring/random intake. Hold this fitted mapping fixed when evaluating different raw queue outcomes; automatic refitting would erase changes to the overall distribution.","limitations":"Fitted to one synthetic month. Per-site distributions are not independently forced. Raw queue values above the fitted support are rejected so severe overload cannot silently be capped. Does not reproduce treatment-resource event timings. No validated causal or clinical interpretation.","live_database_changed":false,"timezone":"Europe/London","category_specific_flag_probabilities":{"fracture_sprain_or_dislocation":0.05,"cuts_or_wounds":0.05,"head_injury_or_neurological_symptoms":0.05,"breathing_problems":0.05,"chest_pain_or_heart_symptoms":0.05,"abdominal_or_stomach_problems":0.05,"other_or_uncategorised":0.05,"unknown":0.05},"comparison_estimates":{"H001":{"bands":{"1":{"mean":129.353594662435,"count":2796},"2":{"mean":125.32687888374797,"count":8232},"3":{"mean":123.99203980948081,"count":10029},"4":{"mean":123.35211423616117,"count":4582},"5":{"mean":128.79509992695725,"count":856},"6":{"mean":121.13995884333019,"count":53},"7":{"mean":54.2169651169,"count":1},"10":{"mean":13.922022810410471,"count":1442}},"pooled":{"mean":119.28397947699104,"count":27991}},"H002":{"bands":{"1":{"mean":120.51528730082042,"count":1234},"2":{"mean":115.06371828145906,"count":3341},"3":{"mean":115.70723406693254,"count":3952},"4":{"mean":110.70824083521414,"count":1860},"5":{"mean":110.4009857642357,"count":339},"6":{"mean":97.00969504163334,"count":15},"10":{"mean":24.021169057087477,"count":559}},"pooled":{"mean":110.49955552178717,"count":11300}},"H003":{"bands":{"1":{"mean":131.37393095246208,"count":625},"2":{"mean":138.30949397270993,"count":1771},"3":{"mean":137.0704056365967,"count":2201},"4":{"mean":130.32911122718082,"count":996},"5":{"mean":126.2987328958503,"count":163},"6":{"mean":123.77363292683846,"count":13},"10":{"mean":52.86251992070909,"count":308}},"pooled":{"mean":131.15550190637327,"count":6077}},"H004":{"bands":{"1":{"mean":129.76859579834974,"count":985},"2":{"mean":129.68606857805827,"count":2763},"3":{"mean":128.74238415583972,"count":3319},"4":{"mean":128.57847835368227,"count":1613},"5":{"mean":123.07909047466,"count":275},"6":{"mean":120.7035409335963,"count":27},"10":{"mean":24.029555324028273,"count":481}},"pooled":{"mean":123.58677951356518,"count":9463}},"H005":{"bands":{"1":{"mean":132.76102027621428,"count":1288},"2":{"mean":125.7224512923153,"count":3757},"3":{"mean":126.57020478773465,"count":4516},"4":{"mean":127.10156452391058,"count":2013},"5":{"mean":117.68682580447827,"count":382},"6":{"mean":108.39582017572307,"count":26},"10":{"mean":36.586177015958334,"count":660}},"pooled":{"mean":122.03001688351893,"count":12642}}},"fitted_model_parameters":{"model_version":"fitted_demo_v11","target_percentages":[5.0,5.0,22.333169472778668,28.788865675310316,22.27233624185818,16.605628610052847],"cumulative_probabilities":[0.05,0.1,0.32333169472778667,0.6112203514808898,0.8339437138994716,1.0],"target_mean_minutes":120.0,"target_median_minutes":100.0,"middle_power":0.8303609889818004,"two_to_four_hour_power":2.0,"outside_training_support":"Raw values above the training maximum are rejected; retain the raw queue result. Not a validated extrapolator.","refit_on_capacity_change":false,"tail_scale_minutes":44.08516290288472},"fitted_model_sha256":"79ed24827331b586ed630ded3c6dc0738cf6152fce7bb29505e9e04c82043912","fitted_model_artifact":"https://github.com/Zack-Aftab/oxhack-project/blob/5f5bfef/simulation/results/fitted-v11/model.json.gz","source_queue_runs":1}$meta$::jsonb,$summary${"model_version":"fitted_demo_v11","synthetic_data":true,"waiting_time_method":"Explicit statistical fit of the user-approved demo distribution, not raw queue waiting time.","generated_patients":67676,"hospital_patients":67473,"emergency_exits":203,"source_queue_statistics":{"count":67473,"mean":140.44710336149936,"median":98.87307041883469,"p90":327.43700404564544,"p95":433.30872136592825,"max":852.8522883733114},"fitted_wait_statistics":{"count":67473,"mean":119.99999999999993,"median":100.0,"p90":262.35546876800004,"p95":292.9097089662399,"max":681.6099600552},"stored_integer_wait_statistics":{"count":67473,"mean":120.50396454878248,"median":100,"p90":263.0,"p95":293.0,"max":682},"target_percentages":[5.0,5.0,22.333169472778668,28.788865675310316,22.27233624185818,16.605628610052847],"wait_bins":[{"label":"10 minutes or less","count":3374,"percent":5.000518726008922},{"label":"Over 10\u201324 minutes","count":3373,"percent":4.9990366516977165},{"label":"Over 24\u201360 minutes","count":15069,"percent":22.33337779556267},{"label":"Over 1\u20132 hours","count":19425,"percent":28.789293495175848},{"label":"Over 2\u20134 hours","count":15028,"percent":22.272612748803226},{"label":"Over 4 hours","count":11204,"percent":16.60516058275162}],"by_hospital":[{"hospital_id":"H001","count":27991,"mean":119.28397947699104,"median":94.9018527497,"p90":266.0340875563,"p95":299.35755227515,"max":681.6099600552},{"hospital_id":"H002","count":11300,"mean":110.49955552178717,"median":93.0566676,"p90":252.64180336767,"p95":284.325260649905,"max":351.3887511366},{"hospital_id":"H003","count":6077,"mean":131.15550190637327,"median":109.7947247056,"p90":273.6293186998001,"p95":306.96300675854,"max":375.393801732},{"hospital_id":"H004","count":9463,"mean":123.58677951356518,"median":105.3298558791,"p90":252.88515458094005,"p95":270.86990435766995,"max":373.483976272},{"hospital_id":"H005","count":12642,"mean":122.03001688351893,"median":104.12743222685,"p90":265.74245542621,"p95":289.65594763417994,"max":353.9737942262}],"bed_waits":{"count":3450,"mean":24.779750571736898,"median":16.22408963585,"p90":31.25573162635,"p95":97.81368185906997,"max":375.393801732},"non_bed_waits":{"count":64023,"mean":125.13112257356735,"median":104.3171550927,"p90":264.51792400280004,"p95":295.1269242252499,"max":681.6099600552},"live_database_changed":false}$summary$::jsonb) on conflict(dataset_id) do update set model_version=excluded.model_version,metadata=excluded.metadata,summary=excluded.summary;
delete from public.demo_fitted_v11_import;
delete from public.demo_capacity_hours where dataset_id='fitted-v11';
delete from public.demo_specialist_hours where dataset_id='fitted-v11';
with profiles as(select key hospital_id,value p from jsonb_each($profiles${"H001":{"hospital_id":"H001","supported_specialties":["cardiology","emergency_medicine","general_surgery_or_gastroenterology","neurology_or_neurosurgery","orthopaedics","respiratory_medicine","wound_care_or_plastics"],"support":{"cardiology":true,"emergency_medicine":true,"general_surgery_or_gastroenterology":true,"neurology_or_neurosurgery":true,"orthopaedics":true,"respiratory_medicine":true,"wound_care_or_plastics":true},"specialist_doctors_on_duty":{"cardiology":3,"emergency_medicine":0,"general_surgery_or_gastroenterology":3,"neurology_or_neurosurgery":4,"orthopaedics":4,"respiratory_medicine":3,"wound_care_or_plastics":4},"general_doctors_by_four_hour_block":[3,5,20,24,34,13],"triage_nurses_by_four_hour_block":[3,2,6,7,7,5],"support_beds":36,"expected_daily_arrivals":933.5111745237411,"expected_general_doctor_utilisation":0.975859935822988,"baseline_general_doctors_by_four_hour_block":[3,5,19,23,34,13],"baseline_support_beds":33,"baseline_fluid_planning_mean_minutes":105.20756918628464,"baseline_fluid_planning_under_30_fraction":0.25399994238046647,"baseline_fluid_end_backlog_work_minutes":534.3070283049401,"general_doctors_by_hour":[14,12,5,12,13,10,9,2,8,12,16,18,19,21,21,23,23,24,24,25,24,22,17,16]},"H002":{"hospital_id":"H002","supported_specialties":["emergency_medicine","orthopaedics","respiratory_medicine","wound_care_or_plastics"],"support":{"cardiology":false,"emergency_medicine":true,"general_surgery_or_gastroenterology":false,"neurology_or_neurosurgery":false,"orthopaedics":true,"respiratory_medicine":true,"wound_care_or_plastics":true},"specialist_doctors_on_duty":{"cardiology":0,"emergency_medicine":0,"general_surgery_or_gastroenterology":0,"neurology_or_neurosurgery":0,"orthopaedics":3,"respiratory_medicine":2,"wound_care_or_plastics":3},"general_doctors_by_four_hour_block":[2,2,8,12,5,6],"triage_nurses_by_four_hour_block":[2,2,3,3,3,2],"support_beds":15,"expected_daily_arrivals":376.6476401625005,"expected_general_doctor_utilisation":0.9910308127526293,"baseline_general_doctors_by_four_hour_block":[2,2,7,11,5,6],"baseline_support_beds":14,"baseline_fluid_planning_mean_minutes":105.6179854964821,"baseline_fluid_planning_under_30_fraction":0.21696996820664868,"baseline_fluid_end_backlog_work_minutes":577.2000964689504,"general_doctors_by_hour":[2,2,2,2,2,2,2,2,7,7,6,8,9,8,8,15,3,8,7,5,7,5,5,5]},"H003":{"hospital_id":"H003","supported_specialties":["cardiology","emergency_medicine","respiratory_medicine"],"support":{"cardiology":true,"emergency_medicine":true,"general_surgery_or_gastroenterology":false,"neurology_or_neurosurgery":false,"orthopaedics":false,"respiratory_medicine":true,"wound_care_or_plastics":false},"specialist_doctors_on_duty":{"cardiology":2,"emergency_medicine":0,"general_surgery_or_gastroenterology":0,"neurology_or_neurosurgery":0,"orthopaedics":0,"respiratory_medicine":2,"wound_care_or_plastics":0},"general_doctors_by_four_hour_block":[2,4,3,4,8,2],"triage_nurses_by_four_hour_block":[2,2,2,2,2,2],"support_beds":8,"expected_daily_arrivals":199.85533217759445,"expected_general_doctor_utilisation":0.9391536997458014,"baseline_general_doctors_by_four_hour_block":[3,3,2,5,6,3],"baseline_support_beds":8,"baseline_fluid_planning_mean_minutes":119.03128964206296,"baseline_fluid_planning_under_30_fraction":0.05016771977779365,"baseline_fluid_end_backlog_work_minutes":656.0543572345562},"H004":{"hospital_id":"H004","supported_specialties":["cardiology","emergency_medicine","general_surgery_or_gastroenterology","wound_care_or_plastics"],"support":{"cardiology":true,"emergency_medicine":true,"general_surgery_or_gastroenterology":true,"neurology_or_neurosurgery":false,"orthopaedics":false,"respiratory_medicine":false,"wound_care_or_plastics":true},"specialist_doctors_on_duty":{"cardiology":2,"emergency_medicine":0,"general_surgery_or_gastroenterology":2,"neurology_or_neurosurgery":0,"orthopaedics":0,"respiratory_medicine":0,"wound_care_or_plastics":2},"general_doctors_by_four_hour_block":[2,2,6,8,13,3],"triage_nurses_by_four_hour_block":[2,2,2,3,3,2],"support_beds":13,"expected_daily_arrivals":318.39206279482033,"expected_general_doctor_utilisation":0.9895611739343881,"baseline_general_doctors_by_four_hour_block":[2,2,5,7,13,3],"baseline_support_beds":12,"baseline_fluid_planning_mean_minutes":114.25414216056636,"baseline_fluid_planning_under_30_fraction":0.1787778936482631,"baseline_fluid_end_backlog_work_minutes":463.101815590332,"general_doctors_by_hour":[2,4,2,5,4,3,2,2,2,6,4,4,8,6,7,7,8,8,8,9,6,6,6,5]},"H005":{"hospital_id":"H005","supported_specialties":["emergency_medicine","general_surgery_or_gastroenterology","neurology_or_neurosurgery","orthopaedics"],"support":{"cardiology":false,"emergency_medicine":true,"general_surgery_or_gastroenterology":true,"neurology_or_neurosurgery":true,"orthopaedics":true,"respiratory_medicine":false,"wound_care_or_plastics":false},"specialist_doctors_on_duty":{"cardiology":0,"emergency_medicine":0,"general_surgery_or_gastroenterology":2,"neurology_or_neurosurgery":3,"orthopaedics":3,"respiratory_medicine":0,"wound_care_or_plastics":0},"general_doctors_by_four_hour_block":[2,3,10,7,16,4],"triage_nurses_by_four_hour_block":[2,2,3,3,3,2],"support_beds":16,"expected_daily_arrivals":415.59178967445456,"expected_general_doctor_utilisation":0.9670424980012914,"baseline_general_doctors_by_four_hour_block":[2,2,7,10,17,4],"baseline_support_beds":15,"baseline_fluid_planning_mean_minutes":143.13933826391445,"baseline_fluid_planning_under_30_fraction":0.16195598398198172,"baseline_fluid_end_backlog_work_minutes":579.5454780639249}}$profiles$::jsonb)), slots as(select t snapshot_at from generate_series(timestamptz '2026-09-21 00:00:00+01',timestamptz '2026-10-20 23:00:00+01',interval '1 hour') t), schedule as(select hospital_id,p,snapshot_at,extract(hour from snapshot_at at time zone 'Europe/London')::integer h from profiles cross join slots)
insert into public.demo_capacity_hours select 'fitted-v11',hospital_id,snapshot_at,snapshot_at+interval '1 hour',case when p?'general_doctors_by_hour' then (p->'general_doctors_by_hour'->>h)::integer else (p->'general_doctors_by_four_hour_block'->>(h/4))::integer end,(p->'triage_nurses_by_four_hour_block'->>(h/4))::integer,(p->>'support_beds')::integer from schedule;
with profiles as(select key hospital_id,value p from jsonb_each($profiles${"H001":{"hospital_id":"H001","supported_specialties":["cardiology","emergency_medicine","general_surgery_or_gastroenterology","neurology_or_neurosurgery","orthopaedics","respiratory_medicine","wound_care_or_plastics"],"support":{"cardiology":true,"emergency_medicine":true,"general_surgery_or_gastroenterology":true,"neurology_or_neurosurgery":true,"orthopaedics":true,"respiratory_medicine":true,"wound_care_or_plastics":true},"specialist_doctors_on_duty":{"cardiology":3,"emergency_medicine":0,"general_surgery_or_gastroenterology":3,"neurology_or_neurosurgery":4,"orthopaedics":4,"respiratory_medicine":3,"wound_care_or_plastics":4},"general_doctors_by_four_hour_block":[3,5,20,24,34,13],"triage_nurses_by_four_hour_block":[3,2,6,7,7,5],"support_beds":36,"expected_daily_arrivals":933.5111745237411,"expected_general_doctor_utilisation":0.975859935822988,"baseline_general_doctors_by_four_hour_block":[3,5,19,23,34,13],"baseline_support_beds":33,"baseline_fluid_planning_mean_minutes":105.20756918628464,"baseline_fluid_planning_under_30_fraction":0.25399994238046647,"baseline_fluid_end_backlog_work_minutes":534.3070283049401,"general_doctors_by_hour":[14,12,5,12,13,10,9,2,8,12,16,18,19,21,21,23,23,24,24,25,24,22,17,16]},"H002":{"hospital_id":"H002","supported_specialties":["emergency_medicine","orthopaedics","respiratory_medicine","wound_care_or_plastics"],"support":{"cardiology":false,"emergency_medicine":true,"general_surgery_or_gastroenterology":false,"neurology_or_neurosurgery":false,"orthopaedics":true,"respiratory_medicine":true,"wound_care_or_plastics":true},"specialist_doctors_on_duty":{"cardiology":0,"emergency_medicine":0,"general_surgery_or_gastroenterology":0,"neurology_or_neurosurgery":0,"orthopaedics":3,"respiratory_medicine":2,"wound_care_or_plastics":3},"general_doctors_by_four_hour_block":[2,2,8,12,5,6],"triage_nurses_by_four_hour_block":[2,2,3,3,3,2],"support_beds":15,"expected_daily_arrivals":376.6476401625005,"expected_general_doctor_utilisation":0.9910308127526293,"baseline_general_doctors_by_four_hour_block":[2,2,7,11,5,6],"baseline_support_beds":14,"baseline_fluid_planning_mean_minutes":105.6179854964821,"baseline_fluid_planning_under_30_fraction":0.21696996820664868,"baseline_fluid_end_backlog_work_minutes":577.2000964689504,"general_doctors_by_hour":[2,2,2,2,2,2,2,2,7,7,6,8,9,8,8,15,3,8,7,5,7,5,5,5]},"H003":{"hospital_id":"H003","supported_specialties":["cardiology","emergency_medicine","respiratory_medicine"],"support":{"cardiology":true,"emergency_medicine":true,"general_surgery_or_gastroenterology":false,"neurology_or_neurosurgery":false,"orthopaedics":false,"respiratory_medicine":true,"wound_care_or_plastics":false},"specialist_doctors_on_duty":{"cardiology":2,"emergency_medicine":0,"general_surgery_or_gastroenterology":0,"neurology_or_neurosurgery":0,"orthopaedics":0,"respiratory_medicine":2,"wound_care_or_plastics":0},"general_doctors_by_four_hour_block":[2,4,3,4,8,2],"triage_nurses_by_four_hour_block":[2,2,2,2,2,2],"support_beds":8,"expected_daily_arrivals":199.85533217759445,"expected_general_doctor_utilisation":0.9391536997458014,"baseline_general_doctors_by_four_hour_block":[3,3,2,5,6,3],"baseline_support_beds":8,"baseline_fluid_planning_mean_minutes":119.03128964206296,"baseline_fluid_planning_under_30_fraction":0.05016771977779365,"baseline_fluid_end_backlog_work_minutes":656.0543572345562},"H004":{"hospital_id":"H004","supported_specialties":["cardiology","emergency_medicine","general_surgery_or_gastroenterology","wound_care_or_plastics"],"support":{"cardiology":true,"emergency_medicine":true,"general_surgery_or_gastroenterology":true,"neurology_or_neurosurgery":false,"orthopaedics":false,"respiratory_medicine":false,"wound_care_or_plastics":true},"specialist_doctors_on_duty":{"cardiology":2,"emergency_medicine":0,"general_surgery_or_gastroenterology":2,"neurology_or_neurosurgery":0,"orthopaedics":0,"respiratory_medicine":0,"wound_care_or_plastics":2},"general_doctors_by_four_hour_block":[2,2,6,8,13,3],"triage_nurses_by_four_hour_block":[2,2,2,3,3,2],"support_beds":13,"expected_daily_arrivals":318.39206279482033,"expected_general_doctor_utilisation":0.9895611739343881,"baseline_general_doctors_by_four_hour_block":[2,2,5,7,13,3],"baseline_support_beds":12,"baseline_fluid_planning_mean_minutes":114.25414216056636,"baseline_fluid_planning_under_30_fraction":0.1787778936482631,"baseline_fluid_end_backlog_work_minutes":463.101815590332,"general_doctors_by_hour":[2,4,2,5,4,3,2,2,2,6,4,4,8,6,7,7,8,8,8,9,6,6,6,5]},"H005":{"hospital_id":"H005","supported_specialties":["emergency_medicine","general_surgery_or_gastroenterology","neurology_or_neurosurgery","orthopaedics"],"support":{"cardiology":false,"emergency_medicine":true,"general_surgery_or_gastroenterology":true,"neurology_or_neurosurgery":true,"orthopaedics":true,"respiratory_medicine":false,"wound_care_or_plastics":false},"specialist_doctors_on_duty":{"cardiology":0,"emergency_medicine":0,"general_surgery_or_gastroenterology":2,"neurology_or_neurosurgery":3,"orthopaedics":3,"respiratory_medicine":0,"wound_care_or_plastics":0},"general_doctors_by_four_hour_block":[2,3,10,7,16,4],"triage_nurses_by_four_hour_block":[2,2,3,3,3,2],"support_beds":16,"expected_daily_arrivals":415.59178967445456,"expected_general_doctor_utilisation":0.9670424980012914,"baseline_general_doctors_by_four_hour_block":[2,2,7,10,17,4],"baseline_support_beds":15,"baseline_fluid_planning_mean_minutes":143.13933826391445,"baseline_fluid_planning_under_30_fraction":0.16195598398198172,"baseline_fluid_end_backlog_work_minutes":579.5454780639249}}$profiles$::jsonb))
insert into public.demo_specialist_hours select c.dataset_id,c.hospital_id,s.key,c.snapshot_at,c.staffing_window_end,case when s.key='emergency_medicine' then c.general_doctors_on_duty else s.value::text::integer end from public.demo_capacity_hours c join profiles p using(hospital_id) cross join lateral jsonb_each(p.p->'specialist_doctors_on_duty') s where c.dataset_id='fitted-v11';

-- One-purpose activation RPC; callable only with the server-side service-role key.
create or replace function public.demo_activate_fitted_v11() returns jsonb
language plpgsql security definer set search_path=pg_catalog,public as $function$
begin
 perform pg_advisory_xact_lock(hashtext('queuecare-fitted-v11'));
 execute $activation$do $wire_check$ begin if (select count(*) from public.demo_fitted_v11_import)<>67676 then raise exception 'Import all 67676 CSV rows before activation'; end if; end $wire_check$;
delete from public.demo_visit_results where dataset_id='fitted-v11';
with decoded as(select *,timestamptz '1970-01-01 00:00:00+00'+(arrival_epoch_microseconds/1000000)*interval '1 second'+(arrival_epoch_microseconds%1000000)*interval '1 microsecond' as arrival from public.demo_fitted_v11_import)
insert into public.demo_visit_results select 'fitted-v11','H'||lpad(origin_code::text,3,'0')||'-'||to_char(arrival at time zone 'Europe/London','YYYY-MM-DD')||'-B'||floor(extract(hour from arrival at time zone 'Europe/London')/4)::text||'-'||lpad(visit_sequence::text,6,'0'),'H'||lpad(origin_code::text,3,'0'),case when destination_code=0 then null else 'H'||lpad(destination_code::text,3,'0') end,arrival,(array['fracture_sprain_or_dislocation','cuts_or_wounds','head_injury_or_neurological_symptoms','breathing_problems','chest_pain_or_heart_symptoms','abdominal_or_stomach_problems','other_or_uncategorised','unknown']::text[])[initial_category_index+1],array(select c from unnest(array['fracture_sprain_or_dislocation','cuts_or_wounds','head_injury_or_neurological_symptoms','breathing_problems','chest_pain_or_heart_symptoms','abdominal_or_stomach_problems','other_or_uncategorised']::text[]) with ordinality categories(c,i) where (category_mask & (1 << (i::integer-1)))<>0),(flags & 1)<>0,pain_score,urgency_rating,(flags & 2)<>0,(flags & 4)<>0,raw_queue_wait_minutes,fitted_demo_wait_minutes,estimated_wait_to_first_doctor_minutes,'fitted_demo_v11' from decoded;
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
$activation$;
 return jsonb_build_object(
  'dataset_id',(select dataset_id from public.demo_active_dataset),
  'hospital_patients',(select count(*) from public.visits),
  'emergency_exits',(select count(*) from public.demo_visit_results where dataset_id='fitted-v11' and is_emergency),
  'fitted_mean_minutes',(select round(avg(fitted_demo_wait_minutes)::numeric,6) from public.visits),
  'fitted_median_minutes',(select percentile_cont(.5) within group(order by fitted_demo_wait_minutes) from public.visits),
  'stored_integer_mean_minutes',(select round(avg(mean_wait_to_first_doctor_minutes)::numeric,6) from public.visits)
 );
end $function$;
revoke all on function public.demo_activate_fitted_v11() from public,anon,authenticated;
grant execute on function public.demo_activate_fitted_v11() to service_role;
notify pgrst,'reload schema';

commit;
select 'Setup complete. Ready for the batch upload.' as status;
