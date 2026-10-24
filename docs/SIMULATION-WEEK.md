> Historical experiment. The selected 30-day model and current commands are in [simulation/README.md](../simulation/README.md).

# QueueCare: one-week doctor-constrained scenario

Five replications were completed for the same 16,158 patients. Each replication starts with three warm-up days (18–20 September 2026), followed by seven measured days (21–27 September). 6,895 warm-up patients per replication were excluded from reported statistics; measured patient-runs total 80,790. Queues and resource use carry continuously from warm-up into the measured week.

**Latest agreed rule.** The `likely_bed_occupancy` flag is known at reception. It identifies the demo's prolonged bed-supported-care cohort and gives nonpreemptive priority to waiting triage and waiting general-doctor queues. It is not assigned during triage and does not interrupt an encounter already underway. The other patients still need a completed general-doctor assessment before leaving. Doctors are shared, with none permanently reserved. This is an explicit simulation prioritisation rule, not a claim that bed need determines clinical urgency.

The flag probability is approximately 5%, with case-dependent probabilities taken from the earlier invented weights and scaled down. 833 patients were flagged (5.16%). There is no separate 3% urgency label in this version.

**Results: reception to first general doctor.**

| Statistic | Individual visits across five runs | Stored per-patient five-run averages |
|---|---:|---:|
| Mean | 140.99 min | 141.49 min |
| Median | 92.07 min | 93 min |
| 90th percentile | 354.58 min | 343 min |
| 95th percentile | 483.70 min | 457 min |

Each patient's five-run average is ceiled once and stored as an integer. The aggregate mean of those integers need not itself be an integer. Individual visits and averaged patient records have different distributions.

| Wait to general doctor | Patient-runs | Percentage |
|---|---:|---:|
| 10 minutes or less | 10,866 | 13.45% |
| Over 10–24 minutes | 8,668 | 10.73% |
| Over 24–60 minutes | 12,709 | 15.73% |
| Over 1–2 hours | 14,577 | 18.04% |
| Over 2–4 hours | 18,581 | 23.00% |
| Over 4 hours | 15,389 | 19.05% |

The earlier monthly v3 model had 30.69% at ten minutes or less; this weekly scenario has 13.45%. Counts are not directly comparable because the periods/populations differ. Some short waits remain because the priority cohort and quiet periods allow rapid contact. There is no imposed minimum wait, copied target distribution or post-processing that stretches samples to make the median larger.

| Replication | Mean, minutes | Median, minutes |
|---|---:|---:|
| 1 | 142.95 | 92.11 |
| 2 | 130.31 | 94.30 |
| 3 | 162.35 | 101.82 |
| 4 | 132.83 | 78.46 |
| 5 | 136.48 | 89.90 |

**Inputs selected before the run.** Expected arrivals remain 450 per site/day, with the previous piecewise-Poisson arrival process, daily intensity variation and weekday assumptions. Realised arrivals averaged 461.66 per site/day. These are unverified synthetic operating assumptions, not measured site-level facts.

| Four-hour window | Effective general doctors | Triage nurses | Expected daily arrival share |
|---|---:|---:|---:|
| 00:00–04:00 | 3 | 2 | 8% |
| 04:00–08:00 | 3 | 2 | 6% |
| 08:00–12:00 | 8 | 3 | 20% |
| 12:00–16:00 | 10 | 3 | 24% |
| 16:00–20:00 | 9 | 3 | 26% |
| 20:00–00:00 | 6 | 2 | 16% |

Mean general-doctor work is twenty minutes, category-dependent and lognormally distributed with coefficient of variation 0.60. Triage service averages 4.5 minutes, lognormal CV 0.45. Each patient completes one general-doctor encounter before being eligible to leave; repeated doctor reassessments and detailed diagnostic workflows are not separately simulated.

There are twenty modelled support spaces per site. A flagged patient requires a space at first general-doctor contact and occupies it for a lognormal mean of twelve hours (CV 0.65), or until the initial doctor assessment ends if that takes longer. Twelve hours is an explicit assumed observation/support duration, not measured admission length or long-term recovery. No separate inpatient admission system is represented. Nonflagged patients do not consume these support spaces; their physical assessment areas are not explicitly constrained.

**Why doctors are the bottleneck.** The roster averages 6.5 effective doctors. At twenty minutes per case, nominal throughput is 468 patients/day against 461.7 arrivals/day. Nominal doctor utilisation is 98.07% and support-space utilisation is 57.97%. Demand peaks and random case durations leave little capacity to clear the queue, including queues inherited from warm-up. This deliberately models a pressured, near-capacity service; it is not an empirically calibrated national average.

A control repeated all five runs with the same population, flags and underlying service-duration draws, adding one effective doctor across every shift (24 clinician-hours per site/day). Mean wait fell to 24.59 minutes and median to 9.83 minutes; utilisation fell to 85.28%. That isolates the staffing mechanism and demonstrates substantial sensitivity. The large reduction is not a promise about hiring one real clinician for one shift.

**Specialty scope.** This version ends its reported wait at first general-doctor contact. It does not simulate or assert specialty availability, specialist queues, rare capability gaps or hospital transfers. The specialist stage was disabled rather than pretending every hospital has every specialty. Initial assessment is distinct from definitive specialist treatment. Subsequent specialist care can be added as a separately specified workflow; it is not included in these figures.

**Validation and limits.** Twenty-two Python tests passed, including new tests for pre-known flag priority at triage and general assessment, no interruption, doctor clearance before departure, exact histogram boundaries and absence of artificial waiting-time floors. All 16,158 stored means were checked against their five finite nonnegative samples and their JSON integer types. There are 840 hourly snapshots, all within the measured week. Impossible required capacity fails instead of manufacturing a finite wait.

No site-specific staffing, bed capacity or actual first-doctor waiting distribution was verified. All five demo sites use the same assumed schedule. The three-day warm-up reduces empty-start bias but does not prove stationarity. Five replications and one measured week do not establish a calibrated confidence interval. Actual urgent triage, resuscitation bypass, individual staff skills/breaks, inpatient flow and patients leaving without care are outside the model.

**Reproduce.**

```sh
python3 scripts/simulate-week.py /path/to/queuecare_mock_dataset_month.json /path/to/new-output-directory
python3 -m unittest discover -s tests -p 'test*.py' -v
```

Seed: 20261025. Outputs include `queuecare_simulated_week.json`, `patient_average_waits.csv`, `summary.json`, `control.json` and `validation.json`. Prior simulations and the original input remain preserved. No live Supabase rows or PR #1 API response shapes were changed; the new schema/model needs explicit integration before replacing the original imported data.
