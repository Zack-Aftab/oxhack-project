> Historical experiment. The selected 30-day model and current commands are in [simulation/README.md](../simulation/README.md).

# QueueCare simulation report — 24 October 2026

**Result:** the revised synthetic baseline produces a **57.5-minute mean** and **21.8-minute median** reception-to-first-doctor wait across all individual patient-runs. After averaging each patient's five waits and rounding that average upwards to an integer, the saved dataset has a **58.0-minute mean** and **26-minute median** across patients.

These are different distributions. The median of five-run patient averages is not the same as the median of individual waits. The mean is above the median because a smaller group experiences long waits during crowded periods. This measures first doctor contact, not discharge, completed treatment or total A&E stay.

**What was executed.** Five continuous 28-day baseline runs, covering 21 September–18 October 2026, with 64,321 fixed measured patients per run and 321,605 measured patient-runs in total. An additional 6,895 warm-up patients per run populate the preceding three days; they are excluded from reported wait statistics. Arrivals, categories, bed/priority flags and specialist-review requirements remain identical across runs. Only triage, clinician, specialist-access and investigation/space-occupation durations change. Five runs of each of four sensitivity scenarios were also completed: 25 month-long runs in total.

**Evidence status.** NHS England and the five trust websites were attempted earlier, but this workspace returned proxy 403 errors. No current site-level activity, staffing, treatment-space or triage distribution was verified. Numbers below are declared engineering assumptions, not estimates fitted to measured hospital data. Real hospital names and locations identify demo sites only. All five receive the same expected demand and resource schedule; differences between sites arise from generated arrivals and case mix, not evidence that one real hospital performs better.

**Inputs and mechanisms.**

| Input | Baseline assumption |
|---|---|
| Expected daily arrivals per hospital | 450; realised mean 459.4 over the measured month |
| Arrival process | Piecewise Poisson arrivals, six four-hour demand windows, 8% daily intensity variation and small illustrative weekday multipliers |
| Arrival shares, midnight onwards | 8%, 6%, 20%, 24%, 26%, 16% |
| Effective concurrent general doctors, same windows | 4, 4, 8, 10, 10, 6; average 7 |
| Triage nurses, same windows | 2, 2, 3, 3, 3, 2 |
| Mean triage service time | 4.5 minutes; actual elapsed arrival-to-triage mean 6.2 minutes including queueing |
| Mean general-doctor service time | 20 minutes, weighted by the source case mix; category-dependent, positively skewed draws |
| Treatment spaces | 20 dedicated modelled spaces; not all hospital beds |
| Mean bed-flagged space occupation | Four hours from first doctor contact, or longer if assessment/specialist work is unfinished |
| Expected bed/priority flag rate | 20%; 12,985 measured cases, averaging 92.75 per hospital/day |
| Expected fraction needing specialist review | 25%; category determines the relevant specialty |
| Specialist access | One concurrent shared-access review slot per specialty; 30-minute mean response plus 20-minute mean consultation |
| Queue policy | Triage first, then nonpreemptive priority; no interruption of treatment already underway |

All duration distributions are lognormal. Coefficients of variation are 0.45 for triage, 0.60 for general-doctor work, 0.50 for specialist work, 0.70 for access response and 0.65 for space holding. These distribution choices are also assumptions.

`likely_bed_occupancy=true` ALSO gives higher priority after triage under the agreed demo rule. Bed need and urgency are not clinically equivalent, and this synthetic flag does not represent an actual clinician assessment. A space-constrained priority patient can still wait; the code never applies a fixed urgency discount. General-doctor contact comes before any specialist review; specialist scarcity influences first-contact waits indirectly when treatment spaces remain occupied. Patients without the flag do not consume these modelled spaces.

Influx is measured from arrivals in the preceding hour at each snapshot. No future arrivals are used as known current influx. Patients remaining after the month ends are followed until completion while staffing continues through normal shift changes.

**Why the baseline average is feasible inside this model.**

Seven average effective doctors providing twenty minutes of work per case yield approximately 504 cases/day of nominal capacity. Realised demand is about 459/day, roughly 91% of that capacity. Busy time measured from the event simulation is 91.0% of nominal doctor capacity. There is enough aggregate capacity to clear demand, but little spare capacity during the busiest windows. Random service durations and arrival surges therefore create meaningful queues.

The bed/priority cohort contributes approximately 92.75 × 4 = 371 treatment-space hours per hospital/day, against 20 × 24 = 480 available space-hours, before specialist-related extensions. Simulated space utilisation is 77.6%. Despite spare average capacity, spaces are all occupied 34.4% of measured time because demand is concentrated and holding times vary. Those episodes delay access for patients who need spaces.

The five baseline run means range from 55.37 to 59.76 minutes. Weekly means are week 1: 54.6 min, week 2: 56.9 min, week 3: 60.0 min, week 4: 58.6 min. The baseline does not exhibit the extreme accumulating backlog seen in the overload scenarios. Warm-up reduces the empty-start bias, but three days and five replications are not proof of a stationary or clinically calibrated model.

This establishes internal resource plausibility. It does **not** establish that 57.5 minutes is the true average at any named hospital. Total-A&E four-hour performance figures cannot validate a first-doctor metric. Measured arrival-to-doctor observations and matching resource data would be required for calibration.

**Baseline distribution.**

| Measure | Individual waits pooled across five runs | Stored per-patient five-run integer averages |
|---|---:|---:|
| Mean | 57.51 min | 58.01 min |
| Median | 21.81 min | 26 min |
| 90th percentile | 158.13 min | 150 min |
| 95th percentile | 234.13 min | 222 min |
| Maximum | 686.94 min | 581 min |

Across individual patient-runs, 28.5% waited more than one hour and 4.8% waited more than four hours before first doctor contact. These are synthetic first-contact statistics, not NHS total-stay performance measures. Rounding is applied once to each patient's five-run mean, never to each raw sample before averaging. Five samples do not provide a calibrated confidence interval for an individual patient.

| Baseline run | Mean wait, min | Median wait, min |
|---|---:|---:|
| 1 | 55.96 | 22.32 |
| 2 | 55.37 | 22.28 |
| 3 | 59.76 | 22.24 |
| 4 | 58.78 | 21.47 |
| 5 | 57.68 | 20.81 |

**Sensitivity checks.** All unchanged patients keep their original identities, arrivals, requirements and random service draws. The higher-arrival scenario adds an independent 20% intensity stream while retaining the original cohort. Its realised increase is 19.8%.

| Scenario | Mean individual wait, min | Median individual wait, min |
|---|---:|---:|
| Baseline | 57.5 | 21.8 |
| One additional effective general doctor per shift | 23.7 | 8.4 |
| One fewer effective general doctor per shift (overloaded) | 1557.8 | 1358.6 |
| 16 treatment spaces instead of 20 | 110.4 | 28.8 |
| Approximately 20% additional arrivals (overloaded) | 2331.4 | 2218.8 |

The one-fewer-doctor schedule has six average effective doctors and approximately 432 cases/day nominal capacity, below the 459/day arrival load. The extra-arrival scenario brings approximately 551/day against 504/day capacity. With no escalation, diversion, abandonment or extra staffing, both scenarios accumulate backlog and produce waits exceeding a day. These are **infeasible sustained operating scenarios**, not realistic predictions of what the NHS would allow unchanged. In-progress work is not interrupted at shift reductions, so busy time can slightly exceed the nominal roster denominator in overload scenarios; this represents implicit finishing-time overrun.

The 16-space scenario operates at about 96% measured space utilisation and has substantially worse tails. The additional-doctor scenario reduces the mean while retaining roughly the same bed loading. Thus the direction of response to resources is sensible, but the large sensitivity demonstrates that the baseline number should not be treated as robust without real calibration.

**Per-site generated results, not real hospital comparisons.** These means and medians are calculated from each patient's unrounded five-run mean.

| Demo site | Patients | Mean, min | Median, min |
|---|---:|---:|---:|
| H001 — simulated The Royal London Hospital | 13,198 | 66.9 | 36.0 |
| H002 — simulated St Mary’s Hospital | 12,788 | 58.9 | 24.9 |
| H003 — simulated University College Hospital | 12,495 | 43.7 | 17.7 |
| H004 — simulated St Thomas’ Hospital | 12,790 | 50.8 | 23.8 |
| H005 — simulated King’s College Hospital | 13,050 | 66.4 | 30.7 |

**Validation and limits.** Nine resource-model tests passed, covering triage-before-contact, priority without interruption, occupied treatment spaces, specialist bottlenecks, added doctor capacity, warm-up exclusion, impossible-resource failure, reproducible draws and shift reductions. Every one of the 64,321 saved patient averages was checked against its five finite nonnegative samples; integer types, timestamps, identities and regenerated population labels were verified. All 3,360 hourly snapshots were checked to lie within the measured month.

Important omitted mechanisms include resuscitation bypass, detailed triage levels, ambulance handover queues, nurse-constrained treatment, individual staff breaks and skills, explicit diagnostic equipment queues, separate inpatient admissions, patients leaving before care, demand changes caused by routing and operational escalation. Bed occupation lumps several downstream delays together. Specialist slots are shared-access approximations, not measured ED staffing. These omissions prevent a claim of real-world accuracy.

**Files and reproduction.**

- `patient_average_waits.csv`: 64,321 patients, five raw waits and an integer mean for each.
- `queuecare_simulated_month.json`: complete generated visits, hospital locations, 3,360 snapshots and explicit assumptions.
- `summary.json`, `sensitivity.json`, `validation.json`: numeric evidence and checks.
- `simulation_results.png` / `simulation_results.pdf`: standalone result figure.

From the repository root:

```sh
python3 scripts/simulate-resource-month.py /path/to/queuecare_mock_dataset_month.json /path/to/new-output-directory
python3 -m unittest discover -s tests -p 'test_resource_month.py' -v
```

Seed: 20261025. Original dataset and previous simulation outputs are preserved. Source SHA-256: `b25f8250d941f7ce6f1a3cd88b7740838f8724ff95a66b608c12c100051c3f05`.

**Database and API status.** These are new simulation artifacts. Supabase still contains the original data; no live tables were overwritten. The PR #1 request/response shapes and its referral-based model remain unchanged. The first-doctor schema, importer and agreed API/model version require coordinated integration before these outputs replace live records.

![Baseline waiting-time distribution and resource loading](/workspace/outputs/queuecare-simulation-v2/simulation_results.png)
