# User-approved fitted demo waits — v11

**This is an explicitly fitted synthetic distribution, not raw queue output or measured NHS waiting times.** The user selected “Fit the synthetic wait distribution to my targets.” The fitted estimate and raw queue wait are separate fields. No live Supabase table or existing API shape was changed.

## Requested distribution and actual result

| Reception to first general doctor | Target | Actual | Patients |
|---|---:|---:|---:|
| 10 minutes or less | 5.00% | 5.00% | 3,374 |
| Over 10–24 minutes | 5.00% | 5.00% | 3,373 |
| Over 24–60 minutes | 22.33% | 22.33% | 15,069 |
| Over 1–2 hours | 28.79% | 28.79% | 19,425 |
| Over 2–4 hours | 22.27% | 22.27% | 15,028 |
| Over 4 hours | 16.61% | 16.61% | 11,204 |

The remaining 90% above 24 minutes is allocated in the same relative proportions as the previous v9 distribution. This preserves those four band proportions, not every within-band quantile from the old model.

Fitted continuous mean: **120.00 minutes**. Median: **100.00 minutes**. After storing each estimate as an integer ceiling, mean: **120.50 minutes**; median: **100 minutes**. There are 67,473 hospital patients and 203 emergency exits; emergency waits remain empty. The source month has three warmup days and 30 measured days, averaging approximately 450 generated arrivals/site/day before specialty routing.

The 90th percentile is 262.36 minutes, the 95th 292.91 and maximum 681.61. These values are properties of the designer distribution, not empirical estimates of a hospital's performance.

## Why the method changed

Doctor/bed-only calibration did not produce the full requested shape. Balanced capacity profiles achieved roughly 9.6% at ten minutes or less, 5.4% over 10–24, a 140.45-minute mean and 98.87-minute median. Prioritising the lowest band too strongly increased over-four-hour waits to approximately 31%. Initial bed-scarcity candidates also produced unacceptable support-bed delays and were excluded from final selection. Those diagnostic results are retained, not presented as accepted profiles.

The selected source uses integer doctor rosters, with staggered hourly coverage at some sites and four-hour coverage at others. Bed capacity is at least the previous 65%-planned-occupancy capacity at each site. The clinician queue remains nonpreemptive; bed cases retain their separate high-priority class, while their stored urgency is 10. Coverage remains explicit true/false, all categories require their mapped staffed specialist, unknown requires self-categorisation, and emergency exits bypass comparison.

## Statistical fit and resource interpretation

One shared monotone transformation maps each raw queue wait's empirical percentile to the requested synthetic quantile curve. It preserves raw-wait ordering and ties across sites. The first three bands use linear quantiles; the one-to-two-hour band's power sets the median to 100 minutes; the two-to-four-hour band uses a power curve; an exponential tail scale sets the mean to 120. The exact fitted parameters and empirical source distribution are saved in model.json.gz.

Doctor availability, beds, urgency, specialties, random service durations, and weekday/time-of-day influx patterns determine the raw queue wait and hence the ordering used by the fit. The fitted value is a new demo estimate; it does **not** equal the source simulation's actual first-doctor event time. This is a designed distribution for the demo, not a clinical or causal model.

Hold the fitted mapping fixed when testing changed capacity. Refitting after every staffing change would force the same aggregate distribution and erase its effect. Values above the source's calibration range are rejected so severe overload cannot silently be capped; use the raw queue result outside support. The mapping is fitted on one synthetic month and has no independent predictive validation.

Bed-priority cases have a fitted median of 16.2 minutes; 62.3% are under 20 minutes. Non-bed cases have a fitted median of 104.3 minutes; 90.3% are over 30 minutes. Priority does not guarantee a maximum wait.

## Selected source capacity

The source model calibrated capacity across multiple configurations using the same patients and service seed. All valid trial records used for selection and diagnostic summaries are under ../distribution-v10. Hourly rosters list 00:00 through 23:00 local time. For sites with four-hour rosters, counts cover 00–04, 04–08, 08–12, 12–16, 16–20 and 20–24. Minimum two active general doctors is preserved. Specialist and triage rosters are unchanged from the source; exact counts are in the source summary.

| Site | Schedule resolution | General doctors on duty | Support beds |
|---|---|---|---:|
| H001 | Hourly | [14, 12, 5, 12, 13, 10, 9, 2, 8, 12, 16, 18, 19, 21, 21, 23, 23, 24, 24, 25, 24, 22, 17, 16] | 36 |
| H002 | Hourly | [2, 2, 2, 2, 2, 2, 2, 2, 7, 7, 6, 8, 9, 8, 8, 15, 3, 8, 7, 5, 7, 5, 5, 5] | 15 |
| H003 | Four-hour blocks | [2, 4, 3, 4, 8, 2] | 8 |
| H004 | Hourly | [2, 4, 2, 5, 4, 3, 2, 2, 2, 6, 4, 4, 8, 6, 7, 7, 8, 8, 8, 9, 6, 6, 6, 5] | 13 |
| H005 | Four-hour blocks | [2, 3, 10, 7, 16, 4] | 16 |

## Files and reproduction

- patient_results.csv: one row per measured patient, with raw_queue_wait_minutes, fitted_demo_wait_minutes, and estimated_wait_to_first_doctor_minutes (integer ceiling).
- dataset.json.gz: full fitted cohort with patient attributes and source capacity profiles.
- model.json.gz: fixed transformation, target percentages and complete empirical queue support.
- ../distribution-v10/dataset.json.gz: untouched source queue results.
- summary.json and metadata.json: actual statistics and explicit method provenance.

From repository root:

```sh
python3 simulation/calibrate_distribution.py simulation/input.json /tmp/replay-queue --rounds 0 --trials-from simulation/results/distribution-v10
python3 simulation/fit_demo_distribution.py /tmp/replay-queue /tmp/replay-fitted
python3 -m unittest discover -s simulation/tests -v
```

Output folders must not exist. A fresh calibration search can instead use --hourly --rounds 24, but the stored trial selection reproduces the published capacity profile. Four search passes (coarse, resumed coarse, hourly, and a high-short-wait-weight diagnostic) preceded the final selection; each capacity configuration used one fixed synthetic month. This was calibration, not repeated independent validation. No fitted records have been imported into Supabase or substituted into the app.
