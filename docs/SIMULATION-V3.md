> Historical experiment. The selected 30-day model and current commands are in [simulation/README.md](../simulation/README.md).

# QueueCare v3 — priority and bed need separated

The endpoint remains reception to first general A&E doctor contact, including triage. This report does not measure time to specialist care, completed treatment, discharge or transfer.

Five 28-day runs were completed for the same 64,321 patients, giving 321,605 measured patient-runs. Another 6,895 patients per run populate the preceding three warm-up days and are excluded from reported waits. Arrivals, categories, bed needs and specialist-review requirements match the v2 cohort exactly.

**The correction.** `clinician_urgent` and `likely_bed_occupancy` are separate booleans. Needing a treatment space no longer grants priority. Priority is applied only after simulated triage and never interrupts ongoing care. The 3% assumption represents a chosen high-priority subgroup, not a verified estimate of all NHS urgent triage categories or a clinically validated resuscitation category.

Urgency probabilities vary mildly with time, weekday and category. The weights are illustrative, not measured risk relationships. They are normalised so expected urgency is exactly 3% across measured arrivals. Separate seeded draws produced 1,987 flagged cases (3.09%). Bed need remained unchanged at 12,985 cases (20.19%). 512 cases have both flags. Separate fields do not imply statistical independence: case mix can affect both.

**Results.**

| Population / statistic | Mean | Median |
|---|---:|---:|
| Individual waits across all five runs | 59.77 min | 24.03 min |
| Stored patient averages, each ceiled after five runs | 60.27 min | 27 min |
| Sensitivity: individual waits with 21 rather than 20 minutes of general-doctor work | 119.82 min | 63.13 min |

The baseline 90th percentile individual wait is 169.3 minutes and the 95th is 242.8 minutes. 29.8% exceed an hour and 5.2% exceed four hours. The higher mean relative to the median reflects a long tail, not universal one-hour waits.

The old combined-flag model had a 57.51-minute mean and 21.81-minute median. Separating the flags changes these to 59.77 and 24.03. Therefore urgency mix was not the main reason for the earlier short median.

**Why capacity matters more.** Resource inputs were deliberately unchanged for the controlled comparison: approximately 459 realised arrivals per hospital/day; effective doctor counts 4,4,8,10,10,6 through the six four-hour windows; twenty minutes of mean general-doctor work; twenty modelled treatment spaces; four-hour mean occupation for patients requiring those spaces; and the v2 triage/specialist assumptions. Nominal doctor utilisation is 91.0% and treatment-space utilisation is 79.4%.

The sensitivity run keeps arrivals, labels, staff, bed inputs and the same underlying random duration draws, increasing general-doctor work by only 5%. Nominal doctor utilisation rises to 95.5%, and waits increase substantially as spare capacity shrinks. This is evidence that the model is sensitive to an uncertain input, not evidence that the higher number is the true hospital wait. The 21-minute scenario is not substituted as the default simply because its median is longer.

**Interpretation.** The current engineering assumptions support a roughly 24-minute median; changing urgency alone does not overturn that. Without measured arrival-to-general-doctor observations and matching resource data, neither the 20- nor 21-minute service assumption is adequately calibrated to the named hospitals. The correct conclusion is an uncertainty range across scenarios, not a newly certified realistic waiting time.

**Known remaining limitations.** The same expected resource schedule applies to all five named sites. Doctor numbers are effective concurrent capacity, not actual headcounts. Non-bed patients implicitly have unlimited chairs/minor-care space. Highest-acuity resuscitation bypass and detailed triage levels are not modelled. V2 universal six-specialty shared-access coverage remains in this controlled comparison; rare capability gaps, specialist transfers and receiving-hospital workloads are not implemented. No actual hospital capability, availability or suitability may be inferred from these outputs. First general-doctor contact does not require a specialist to be present, but downstream resource bottlenecks can still affect the queue.

**Reproduction and validation.**

```sh
python3 scripts/simulate-priority-month.py /path/to/queuecare_mock_dataset_month.json /path/to/new-output-directory
python3 -m unittest discover -s tests -p 'test_*month.py' -v
```

Seed 20261025. Eighteen Python simulation tests passed, including new tests that bed need does not grant priority and that variable urgency probabilities average to exactly 3%. Six importer tests also passed. All 64,321 patient means were verified as `ceil(mean(five raw waits))` and as JSON integers. The original cohort attributes were checked against v2.

The new JSON and CSV contain both flags and all five samples. Older outputs are preserved. The pending local label migration now defines separate nullable fields; it has not been applied to Supabase. Existing database rows have no real clinician-recorded labels and should not be silently labelled nonurgent. The original importer is for the original source format, not this generated schema.

**No Supabase data or shared API response shapes were changed.** These are generated simulation artifacts. PR #1 integration still needs a coordinated schema/import/model update; this work does not silently reinterpret its referral endpoint as first-doctor contact.
