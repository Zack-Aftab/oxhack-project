begin;
alter table public.visits
  add column pain_score smallint check (pain_score between 1 and 10),
  add column urgency_rating smallint check (urgency_rating between 1 and 10),
  add column is_emergency boolean,
  add column urgency_assessment_source text check (urgency_assessment_source = 'gemini_demo'),
  add column urgency_model text,
  add column urgency_assessed_at timestamptz,
  add column urgency_reason text,
  add constraint visits_gemini_emergency_rating_check
    check (is_emergency is not true or (urgency_rating is not null and urgency_rating = 10));
comment on column public.visits.urgency_rating is
  'Unvalidated Gemini demo estimate, 1 least concern to 10 greatest concern; not clinician triage or a predicted wait. NULL means not assessed or insufficient information.';
comment on column public.visits.pain_score is
  'Patient self-reported pain 1-10; not inferred from a photo or a default. NULL means not supplied.';
comment on column public.visits.is_emergency is
  'AI-suspected emergency, not a diagnosis. False means no warning signs identified in the supplied input, not medical clearance. NULL means unassessed/insufficient information.';
notify pgrst, 'reload schema';
commit;
