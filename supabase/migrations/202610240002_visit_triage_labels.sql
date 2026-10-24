begin;

-- Pending migration; original source visits have no recorded clinical labels.
alter table public.visits
  add column likely_bed_occupancy boolean,
  add column clinician_urgent boolean;

comment on column public.visits.likely_bed_occupancy is
  'Expected need for an ED treatment space. Separate from clinical urgency. NULL means unrecorded; generated simulation labels are fictional.';
comment on column public.visits.clinician_urgent is
  'Clinician-assigned priority after triage. Separate from bed need. NULL means unrecorded; generated simulation labels are fictional, not actual clinical assessments.';

notify pgrst, 'reload schema';
commit;
