-- Apply once to the EXISTING QueueCare demo project, after the backup command.
-- Preserves the four original tables and all their data in a private archive.
-- New public tables are initially empty; run simulation/database.mjs to load them.
begin;
create schema queuecare_archive_20261024;
revoke all on schema queuecare_archive_20261024 from public, anon, authenticated;
alter table public.simulation_scenarios set schema queuecare_archive_20261024;
alter table public.visits set schema queuecare_archive_20261024;
alter table public.staffing_snapshots set schema queuecare_archive_20261024;
alter table public.hospitals set schema queuecare_archive_20261024;

create table public.hospitals (
  hospital_id text primary key,
  name text not null,
  address text not null,
  latitude double precision not null check (latitude between -90 and 90),
  longitude double precision not null check (longitude between -180 and 180)
);

create table public.visits (
  visit_id text primary key,
  hospital_id text not null references public.hospitals(hospital_id),
  arrival_at timestamptz not null,
  complaint_category text not null,
  likely_bed_occupancy boolean not null,
  mean_wait_to_first_doctor_minutes integer not null check (mean_wait_to_first_doctor_minutes >= 0),
  mean_first_doctor_at timestamptz not null,
  simulation_waits_minutes double precision[] not null,
  simulation_run_count integer not null check (simulation_run_count = 5),
  min_wait_to_first_doctor_minutes double precision not null check (min_wait_to_first_doctor_minutes >= 0),
  max_wait_to_first_doctor_minutes double precision not null check (max_wait_to_first_doctor_minutes >= min_wait_to_first_doctor_minutes),
  wait_stddev_minutes double precision not null check (wait_stddev_minutes >= 0),
  check (cardinality(simulation_waits_minutes) = 5 and array_ndims(simulation_waits_minutes) = 1),
  check (array_position(simulation_waits_minutes, null) is null),
  check (0 <= all(simulation_waits_minutes) and 'Infinity'::double precision > all(simulation_waits_minutes)),
  check (mean_wait_to_first_doctor_minutes = ceil((simulation_waits_minutes[1] + simulation_waits_minutes[2] + simulation_waits_minutes[3] + simulation_waits_minutes[4] + simulation_waits_minutes[5]) / 5)),
  check (mean_first_doctor_at = arrival_at + mean_wait_to_first_doctor_minutes * interval '1 minute')
);
create index visits_hospital_arrival_idx on public.visits (hospital_id, arrival_at);
comment on column public.visits.likely_bed_occupancy is
  'Synthetic prolonged-support-bed flag known at reception. Grants nonpreemptive triage and general-doctor queue priority under the selected demo rule; not a real clinical urgency assessment.';
comment on column public.visits.complaint_category is
  'Stable category ID retained for the agreed API; display labels belong in the API catalog, not duplicated per visit.';

create table public.staffing_snapshots (
  snapshot_id text primary key,
  hospital_id text not null references public.hospitals(hospital_id),
  snapshot_at timestamptz not null,
  staffing_window_end timestamptz not null,
  general_doctors_available integer not null check (general_doctors_available >= 0),
  triage_nurses_available integer not null check (triage_nurses_available >= 0),
  beds_available integer not null check (beds_available >= 0),
  observed_arrivals_last_hour integer not null check (observed_arrivals_last_hour >= 0),
  mean_general_doctors_free double precision not null check (mean_general_doctors_free >= 0),
  mean_beds_free double precision not null check (mean_beds_free >= 0),
  mean_waiting_for_first_doctor double precision not null check (mean_waiting_for_first_doctor >= 0),
  mean_waiting_for_triage double precision not null check (mean_waiting_for_triage >= 0),
  unique (hospital_id, snapshot_at),
  check (staffing_window_end = snapshot_at + interval '1 hour')
);
comment on column public.staffing_snapshots.observed_arrivals_last_hour is
  'Measured arrivals during the previous hour, not a prediction of future influx.';

create table public.simulation_datasets (
  dataset_id text primary key,
  model_version text not null,
  metadata jsonb not null,
  summary jsonb not null,
  imported_at timestamptz not null default now()
);

alter table public.hospitals enable row level security;
alter table public.visits enable row level security;
alter table public.staffing_snapshots enable row level security;
alter table public.simulation_datasets enable row level security;
revoke all on public.hospitals, public.visits, public.staffing_snapshots, public.simulation_datasets from anon, authenticated;
grant select, insert, update, delete on public.hospitals, public.visits, public.staffing_snapshots, public.simulation_datasets to service_role;
notify pgrst, 'reload schema';
commit;
