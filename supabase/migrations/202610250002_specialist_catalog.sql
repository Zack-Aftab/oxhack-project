-- Additive specialist demo schema. Does not overwrite the existing monthly data.
begin;
create table public.specialties (
 specialty_id text primary key,
 label text not null
);
create table public.category_specialties (
 category_id text primary key,
 specialty_id text not null references public.specialties(specialty_id),
 requires_manual_selection boolean not null default false
);
create table public.hospital_specialties (
 hospital_id text not null references public.hospitals(hospital_id),
 specialty_id text not null references public.specialties(specialty_id),
 supported boolean not null,
 primary key(hospital_id,specialty_id)
);
create table public.specialist_staffing (
 hospital_id text not null,
 specialty_id text not null,
 shift_start timestamptz not null,
 shift_end timestamptz not null check(shift_end>shift_start),
 doctors_on_duty integer not null check(doctors_on_duty>=0),
 primary key(hospital_id,specialty_id,shift_start),
 foreign key(hospital_id,specialty_id) references public.hospital_specialties(hospital_id,specialty_id)
);
create index specialist_staffing_window_idx on public.specialist_staffing(shift_start,shift_end);
create table public.specialist_simulation_visits (
 dataset_id text not null references public.simulation_datasets(dataset_id),
 visit_id text not null,
 origin_hospital_id text not null references public.hospitals(hospital_id),
 hospital_id text references public.hospitals(hospital_id),
 arrival_at timestamptz not null,
 initial_category text not null references public.category_specialties(category_id),
 complaint_categories text[] not null check(cardinality(complaint_categories) between 0 and 7),
 required_specialties text[] not null,
 likely_bed_occupancy boolean not null,
 pain_score smallint not null check(pain_score between 1 and 10),
 urgency_rating double precision not null check(urgency_rating between 1 and 10),
 is_emergency boolean not null,
 manual_category_confirmation boolean not null,
 simulation_waits_minutes double precision[] not null,
 mean_wait_to_first_doctor_minutes integer,
 primary key(dataset_id,visit_id),
 check(not likely_bed_occupancy or urgency_rating=10),
 check(array_position(complaint_categories,null) is null and not ('unknown'=any(complaint_categories))),
 check(array_position(simulation_waits_minutes,null) is null),
 check(cardinality(simulation_waits_minutes)=0 or array_ndims(simulation_waits_minutes)=1),
 check((is_emergency and urgency_rating=10 and hospital_id is null and mean_wait_to_first_doctor_minutes is null and cardinality(simulation_waits_minutes)=0)
    or (not is_emergency and cardinality(complaint_categories)>=1 and hospital_id is not null and mean_wait_to_first_doctor_minutes is not null and mean_wait_to_first_doctor_minutes>=0 and cardinality(simulation_waits_minutes)=5)),
 check(0<=all(simulation_waits_minutes) and 'Infinity'::double precision>all(simulation_waits_minutes)),
 check(is_emergency or mean_wait_to_first_doctor_minutes=ceil((simulation_waits_minutes[1]+simulation_waits_minutes[2]+simulation_waits_minutes[3]+simulation_waits_minutes[4]+simulation_waits_minutes[5])/5))
);
create index specialist_visits_hospital_time_idx on public.specialist_simulation_visits(hospital_id,arrival_at);
comment on column public.specialist_simulation_visits.urgency_rating is 'Synthetic float 1-10, not clinical triage. Bed-support flag forces 10; 10 alone does not imply emergency.';
comment on table public.hospital_specialties is 'Complete explicit true/false demo matrix. Hypothetical coverage, not verified NHS capabilities.';
comment on table public.specialist_staffing is 'On-duty capacity, not the number currently idle. General/emergency medicine uses the general-doctor pool.';
alter table public.specialties enable row level security;
alter table public.category_specialties enable row level security;
alter table public.hospital_specialties enable row level security;
alter table public.specialist_staffing enable row level security;
alter table public.specialist_simulation_visits enable row level security;
revoke all on public.specialties,public.category_specialties,public.hospital_specialties,public.specialist_staffing,public.specialist_simulation_visits from anon,authenticated;
grant select,insert,update,delete on public.specialties,public.category_specialties,public.hospital_specialties,public.specialist_staffing,public.specialist_simulation_visits to service_role;
notify pgrst,'reload schema';
commit;
