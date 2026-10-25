# One additional doctor and adjusted bed capacity — v9

Thirty measured days with three warmup days, using exactly the same cohort, arrival times, categories, routing, pain, urgency, bed flags and random service-duration seed as v8. All profiles and operating data are synthetic. No Supabase changes or API activation were performed.

## Result and target

| Scenario | Mean minutes | Median minutes |
|---|---:|---:|
| Previous v8 | 176.6 | 119.6 |
| Extra doctor around the clock + adjusted beds (diagnostic) | 54.8 | 23.8 |
| One additional doctor 08–16 daily + adjusted beds (selected) | 108.7 | 70.1 |
| Requested target | about 120 | about 100 |

The selected result misses the median target by about 30 minutes; the mean is 11.3 minutes below target. These are actual queue outputs, not adjusted or clipped waits. The median target has not been achieved. The 24-hour diagnostic adds 24 doctor-hours/site/day, whereas the selected staffing interpretation adds one eight-hour doctor shift/site/day. The diagnostic is retained in diagnostic-24h-summary.json. Two capacity checks were run and both are disclosed; no seed or patient cohort was selected to fit the desired numbers.

The extra doctor has a large effect because baseline capacity was close to saturation. At a small hospital, one additional active doctor is a large percentage increase, and clearing a backlog can reduce waits nonlinearly. This is a consequence of the invented model, not evidence of how a real hospital would respond. More beds mainly improve bed-priority access; they do not directly supply more general-doctor time for everyone else.

There are 67,676 measured generated patients, including 203 emergency exits and 67,473 hospital attendances. Each hospital patient has one raw wait and its integer ceiling; this run is not a five-run average. Bed need remains approximately 5%, stored bed urgency is 10 and the separate priority tier is 15. There is no mandatory floor for ordinary waits and no forced normal distribution.

| Group | Mean | Median | 90th percentile |
|---|---:|---:|---:|
| All hospital patients | 108.7 | 70.1 | 280.9 |
| Non-bed patients | 113.5 | 76.3 | 287.5 |
| Bed-priority patients | 19.5 | 6.8 | 26.2 |

72.6% of non-bed patients wait over 30 minutes; 87.4% of bed-priority cases are seen within 20 minutes.

## Capacity adjustment

General rosters show simultaneous doctors for 00–04, 04–08, 08–12, 12–16, 16–20 and 20–24 local time. One doctor is added in the two 08–16 blocks at every site, including warmup days. Bed capacity uses ceil(expected_daily_arrivals × 5% × 12/24 ÷ 65%), with minimum eight beds, rather than the previous 72% occupancy target. The 65% figure is a planning assumption, not an observed occupancy statistic. Triage and specialist rosters and all service-time assumptions remain unchanged. Actual utilisation is in summary.json.

| Site | Previous general roster | New general roster | Beds before → after | Mean / median wait |
|---|---|---|---|---|
| H001 | [3, 5, 19, 23, 34, 13] | [3, 5, 20, 24, 34, 13] | 33 → 36 | 112.0 / 64.8 min |
| H002 | [2, 2, 7, 11, 5, 6] | [2, 2, 8, 12, 5, 6] | 14 → 15 | 98.7 / 65.8 min |
| H003 | [3, 3, 2, 5, 6, 3] | [3, 3, 3, 6, 6, 3] | 8 → 8 | 84.1 / 53.6 min |
| H004 | [2, 2, 5, 7, 13, 3] | [2, 2, 6, 8, 13, 3] | 12 → 13 | 97.1 / 67.5 min |
| H005 | [2, 2, 7, 10, 17, 4] | [2, 2, 8, 11, 17, 4] | 15 → 16 | 130.6 / 95.9 min |

## Wait distribution

| Reception to first general doctor | Patients | Percentage |
|---|---:|---:|
| 10 minutes or less | 13,287 | 19.7% |
| Over 10–24 minutes | 5,364 | 7.9% |
| Over 24–60 minutes | 12,115 | 18.0% |
| Over 1–2 hours | 15,617 | 23.1% |
| Over 2–4 hours | 12,082 | 17.9% |
| Over 4 hours | 9,008 | 13.4% |

## Reproduce

```sh
python3 simulation/demand_patterns.py simulation/input.json /tmp/capacity-v9 --extra-general-doctors 1 --doctor-shift-start 8 --bed-target-occupancy .65
```

For the 24-hour diagnostic, omit --doctor-shift-start. The seed defaults to 20261027. The output folder must not already exist. Source and results are preserved alongside v8, whose output is unchanged. These one-sample rows are not compatible with the existing five-sample SQL import constraint without a separate migration. No source/contract or live database change was made.
