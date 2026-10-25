begin;

create table public.hospitals (
  hospital_id text primary key,
  name text not null,
  address text not null,
  latitude double precision not null check (latitude between -90 and 90),
  longitude double precision not null check (longitude between -180 and 180),
  nhs_source text,
  ae_source text,
  simulation_profile text,
  synthetic_load_factor double precision check (synthetic_load_factor > 0),
  synthetic_specialty_profile text,
  is_synthetic boolean not null default true check (is_synthetic)
);

create table public.visits (
  visit_id text primary key,
  hospital_id text not null references public.hospitals(hospital_id),
  arrival_at timestamptz not null,
  complaint_category text not null,
  complaint_category_label text not null,
  required_specialty_for_demo_model text not null,
  wait_reception_to_doctor_referral_minutes integer not null check (wait_reception_to_doctor_referral_minutes >= 0),
  wait_doctor_referral_to_diagnosis_minutes integer not null check (wait_doctor_referral_to_diagnosis_minutes >= 0),
  estimated_total_arrival_to_diagnosis_minutes integer not null,
  referral_at timestamptz not null,
  diagnosis_at timestamptz not null,
  check (estimated_total_arrival_to_diagnosis_minutes = wait_reception_to_doctor_referral_minutes + wait_doctor_referral_to_diagnosis_minutes),
  check (referral_at = arrival_at + wait_reception_to_doctor_referral_minutes * interval '1 minute'),
  check (diagnosis_at = referral_at + wait_doctor_referral_to_diagnosis_minutes * interval '1 minute')
);
create index visits_hospital_arrival_idx on public.visits (hospital_id, arrival_at);

create table public.staffing_snapshots (
  snapshot_id text primary key,
  hospital_id text not null references public.hospitals(hospital_id),
  snapshot_at timestamptz not null,
  staffing_window_end timestamptz not null check (staffing_window_end > snapshot_at),
  general_doctors_available integer not null check (general_doctors_available >= 0),
  specialty_doctors_available jsonb not null check (jsonb_typeof(specialty_doctors_available) = 'object'),
  beds_available integer not null check (beds_available >= 0),
  patients_waiting_for_doctor_referral integer not null check (patients_waiting_for_doctor_referral >= 0),
  patients_waiting_for_diagnosis integer not null check (patients_waiting_for_diagnosis >= 0),
  arrivals_during_next_4h integer not null check (arrivals_during_next_4h >= 0),
  simulated_staffing_status text not null,
  staffing_status_basis text not null,
  unique (hospital_id, snapshot_at)
);

-- Isolated what-if settings. Historical records are never edited by a slider.
create table public.simulation_scenarios (
  scenario_id uuid primary key default gen_random_uuid(),
  name text not null,
  base_snapshot_id text not null references public.staffing_snapshots(snapshot_id),
  general_doctors_available integer not null check (general_doctors_available >= 0),
  specialty_doctors_available jsonb not null check (jsonb_typeof(specialty_doctors_available) = 'object'),
  beds_available integer not null check (beds_available >= 0),
  patients_waiting_for_doctor_referral integer not null check (patients_waiting_for_doctor_referral >= 0),
  patients_waiting_for_diagnosis integer not null check (patients_waiting_for_diagnosis >= 0),
  simulated_arrivals_next_4h integer not null check (simulated_arrivals_next_4h >= 0),
  created_at timestamptz not null default now()
);

-- No public policies: browser clients cannot read or modify these tables.
-- Only trusted backend code uses the server secret. Authenticate dashboard writes there.
alter table public.hospitals enable row level security;
alter table public.visits enable row level security;
alter table public.staffing_snapshots enable row level security;
alter table public.simulation_scenarios enable row level security;
revoke all on public.hospitals, public.visits, public.staffing_snapshots, public.simulation_scenarios from anon, authenticated;
grant select, insert, update, delete on public.hospitals, public.visits, public.staffing_snapshots, public.simulation_scenarios to service_role;
commit;
