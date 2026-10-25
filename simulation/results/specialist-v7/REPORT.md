# Specialist and urgency simulation: actual results

These are invented demonstration profiles, not verified services or measured waits at the real hospitals whose IDs were retained. This model is not calibrated to NHS waiting-time data.

## Cohort and endpoint

Three warmup days, then 30 measured days (21 September–20 October 2026), repeated five times for the same patients. 67,346 measured patients were generated; 221 synthetic emergency cases exited to the call-999 flow. The other 67,125 patients each have five waits and one stored integer: ceil(mean(five waits)). The endpoint is arrival at reception to first general doctor, including triage; subsequent specialist review is simulated but excluded from this wait.

There are 3,367 bed flags (5.00% including seven emergency cases), 13,445 multi-category patients, 3,232 simulated manual self-categorisations and 27,408 patients assigned to a different eligible site before arrival. These manual choices are fictional inputs, not AI decisions. Emergency exits need no category confirmation.

## Results

Raw patient-run mean: **90.25 minutes**; median: **26.04 minutes**. The 90th percentile is 265.06 minutes, 95th 386.74, and maximum 1,024.90. Across the 67,125 stored patient averages, the mean is **90.75 minutes**, median **33**, 90th percentile 262 and maximum 852. A median of patient averages differs from a median of individual runs.

| Reception to first general doctor | Patient-runs | Percentage |
|---|---:|---:|
| 10 minutes or less | 122,125 | 36.4% |
| Over 10–24 minutes | 42,522 | 12.7% |
| Over 24–60 minutes | 42,382 | 12.6% |
| Over 1–2 hours | 47,373 | 14.1% |
| Over 2–4 hours | 42,338 | 12.6% |
| Over 4 hours | 38,885 | 11.6% |

**36.4% remain at ten minutes or less.** This is an output of the assumed rosters, arrival pattern and queue discipline; it is not evidence that those waits are realistic. A long tail raises the mean above the median. Further calibration needs an observed distribution of first-clinician waits and actual active doctor-hours, not just a desired mean. The previous model's numbers are not a controlled comparison because routing, staffing and queue discipline changed together.

## Urgency and specialty rules

Each confirmed category requires exactly one modelled doctor type; every required type must be supported and staffed at the hospital. Multiple categories use AND matching. Unknown is blocked until the patient selects a known category. Other/uncategorised maps to general emergency medicine; unknown has a display mapping only and is never accepted as a clinical requirement.

| Category | Required demo doctor type |
|---|---|
| Fracture/sprain/dislocation | Orthopaedics |
| Cuts/wounds | Wound care/plastics |
| Head injury/neurological | Neurology/neurosurgery |
| Breathing | Respiratory medicine |
| Chest/heart | Cardiology |
| Abdominal/stomach | General surgery/gastroenterology |
| Other/uncategorised | General emergency medicine |
| Unknown | Must self-categorise before comparison |

Urgency is a synthetic float from 1 to 10, rounded to two decimals, influenced by category and synthetic pain score. A bed flag forces 10 and gives priority at triage and subsequent queues. Emergency is a separate flag: bed occupancy alone does not trigger call 999. Treatment already in progress is not interrupted. Among non-bed patients, queue priority gains one point per 30 minutes waiting; stored urgency does not change. This prevents starvation. The archived strict-priority diagnostic produced a roughly 21-day maximum wait and was rejected.

| Urgency | Patients | Mean wait, minutes | Median wait, minutes |
|---|---:|---:|---:|
| 1–3 | 7,364 | 136.5 | 93.4 |
| Over 3–6 | 43,474 | 97.2 | 37.7 |
| Over 6–9.99 | 12,927 | 60.4 | 8.9 |
| 10 | 3,360 | 13.7 | 6.4 |

## Capacity assumptions and hospital outcomes

Each source catchment has 450 expected daily arrivals before eligible routing, with 8% daily intensity variation, weekday multipliers and time-of-day variation. Patients retain the origin if eligible; otherwise a seeded random eligible site is selected. This is not a feedback simulation of users following fastest-hospital recommendations.

Mean service times: triage 4.5 minutes; general doctor approximately 20 minutes after case-mix normalisation; each required specialist 20 minutes; bed support 12 hours. Durations are lognormal. Specialist consultations follow the first general encounter sequentially. Beds are support beds, not total hospital beds. Each site's general roster is planned from expected doctor work after routing; specialist pools target at most 80% nominal utilisation. Actual measured general utilisation is 92.9–97.8%.

General rosters below are on-duty counts for 00–04, 04–08, 08–12, 12–16, 16–20, 20–24 local time. Specialist counts are constant across shifts. General emergency medicine uses the general pool, so its separate specialist count is zero internally and its exported staffed count is the general roster.

| Site | General roster | Support beds | Specialist counts excluding general medicine | Mean / median wait |
|---|---|---:|---|---|
| H001 | [6, 6, 16, 20, 18, 12] | 38 | cardiology: 3, general_surgery_or_gastroenterology: 3, neurology_or_neurosurgery: 4, orthopaedics: 3, respiratory_medicine: 3, wound_care_or_plastics: 3 | 49.4 / 12.2 min |
| H002 | [2, 2, 6, 7, 8, 4] | 18 | orthopaedics: 3, respiratory_medicine: 2, wound_care_or_plastics: 3 | 60.6 / 16.7 min |
| H003 | [2, 2, 5, 6, 5, 3] | 11 | cardiology: 2, respiratory_medicine: 2 | 127.3 / 73.8 min |
| H004 | [2, 2, 6, 8, 7, 5] | 16 | cardiology: 2, general_surgery_or_gastroenterology: 2, wound_care_or_plastics: 3 | 49.6 / 14.5 min |
| H005 | [3, 3, 7, 9, 8, 6] | 19 | general_surgery_or_gastroenterology: 2, neurology_or_neurosurgery: 3, orthopaedics: 3 | 210.5 / 154.0 min |

H001 is the full-coverage hub. Other sites have unique subsets. All 35 hospital/specialty coverage cells are explicit booleans; no unknown coverage. All 67,125 queued patients pass complete specialty matching. General medicine is supported everywhere. A full hub guarantees capability coverage for every known combination, not unlimited instantaneous capacity.

## Deliverables and activation

Source, archived diagnostic, tests, compressed full cohort, integer results, capability matrix, additive SQL migration and rerunnable profile/staffing/summary seed are included in the repository. SQL was checked with PostgreSQL-compatible PGlite, including all 67,346 optional raw visits, repeat seeding, coverage, bed urgency constraints and denied anonymous reads.

The opt-in POST /api/compare/multi contract accepts complaintCategories[], numeric urgencyRating, likelyBedOccupancy and isEmergency. It gates emergency and unknown before database access, excludes hospitals lacking any required staffed specialty, and ranks eligible sites by illustrative travel plus a retrospective hospital/urgency-band mean. This is not an individual clinical prediction or a new queue simulation per request. Fixtures and typed live/sample client adapters are supplied; existing frontend screens still need to opt in.

The live Supabase database has not been changed for this version. Apply supabase/migrations/202610250002_specialist_catalog.sql, then simulation/results/specialist-v7/seed.sql after restoring a valid server-side Supabase credential. The seed adds capabilities, staffing and versioned summary metadata without replacing the active monthly dataset; the full raw cohort is a separate optional import. The live normal comparison cannot work until those tables and metadata are seeded. No original shared endpoint shape was changed.
