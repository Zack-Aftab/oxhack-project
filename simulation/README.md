# Specialist simulation

Current model: `specialists.py`, version specialist_urgency_v7. Read [the actual results and limitations](results/specialist-v7/REPORT.md). These are synthetic capability profiles and case histories, not real hospital service claims.

Reproduce from repository root using Python 3.11+ (standard library only):

```sh
python3 simulation/specialists.py simulation/input.json /tmp/specialist-results
python3 simulation/export_specialists.py /tmp/specialist-results
python3 -m unittest discover -s simulation/tests -v
```

Defaults use three warmup days, 30 measured days and five repetitions of the same patient cohort. `--help` lists optional settings. Current results retain five raw waits per completed patient and ceil their mean to an integer. Emergency exits have no hospital or wait. The archive contains a rejected strict-priority diagnostic, not the selected model.

The additive Supabase migration is `supabase/migrations/202610250002_specialist_catalog.sql`. The checked, rerunnable seed is `results/specialist-v7/seed.sql`. Apply migration before seed; these are prepared artifacts, not an assertion of live deployment. The seed includes capacity/staffing and summary metadata; full visits remain in `dataset.json.gz` for a separate optional import. Existing active monthly data is preserved.

## New single-run demand evaluation

`demand_patterns.py` adds unequal catchment demand, recurring weekday/category patterns, stochastic arrivals, lower ordinary urgency and a separate bed-priority tier. Run once with three warmup days and 30 measured days:

```sh
python3 simulation/demand_patterns.py simulation/input.json /tmp/new-demand-run
```

Read [v8 actual results](results/demand-v8/REPORT.md): median 119.6 minutes, mean 176.6 minutes. The two-hour mean target was missed; no forced normal waits or repeated stochastic runs were used to conceal this. V8 remains an offline evaluation, with previous v7 live adapters and seed unchanged.

## Additional-doctor capacity check

[Capacity v9 results](results/capacity-v9/REPORT.md) retain the same v8 patients and service seed. One additional 08–16 doctor/site/day and a 65% planned bed-occupancy target yield mean 108.7 and median 70.1 minutes; the requested 120/100 target is not fully reached. The initial 24-hour extra-doctor check is disclosed in the report.

```sh
python3 simulation/demand_patterns.py simulation/input.json /tmp/capacity-v9 --extra-general-doctors 1 --doctor-shift-start 8 --bed-target-occupancy .65
```

## User-approved fitted demo distribution

Latest display estimates: [fitted v11 report](results/fitted-v11/REPORT.md). They explicitly fit the requested 5% / 5% / proportional remaining bands, mean120 and median100. Raw queue results remain separate under `results/distribution-v10`; fitted values do not claim to be raw simulation event times. Freeze the transformation for capacity comparisons rather than refitting each scenario. Nothing was imported into Supabase.

```sh
python3 simulation/calibrate_distribution.py simulation/input.json /tmp/replay-queue --rounds 0 --trials-from simulation/results/distribution-v10
python3 simulation/fit_demo_distribution.py /tmp/replay-queue /tmp/replay-fitted
```

All candidate searches and their limits are disclosed in the report. Stored trial records reproduce the selected source capacity without repeating the search. `fit_demo_distribution.py` uses only the Python standard library.
