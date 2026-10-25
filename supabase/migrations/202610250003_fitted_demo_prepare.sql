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
