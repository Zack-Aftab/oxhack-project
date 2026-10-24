> Historical experiment. The selected 30-day model and current commands are in [simulation/README.md](../simulation/README.md).

# Five-run monthly simulation

This documents the archived v1 run. The revised resource model, results and sensitivity analysis are in [SIMULATION-V2.md](SIMULATION-V2.md).

`simulate-month.py` is a dependency-free, offline data-generation tool. It does not write to Supabase or change the shared TypeScript API. The runtime app remains Next.js/Node.js; Python is only used to generate synthetic data.

From the repository root:

```sh
python3 scripts/simulate-month.py /path/to/queuecare_mock_dataset_month.json /path/to/new-output-directory
python3 -m unittest discover -s tests -p 'test_simulate_month.py' -v
```

The output directory must not already contain generated results. The source is read-only and its SHA-256 is recorded. Output contains `queuecare_simulated_month.json` and `summary.json`.

## Fixed patient population, five replications

- Reuse all 42,000 IDs, hospitals, arrival timestamps, complaint IDs and specialty assignments from the supplied 28-day dataset (21 September–18 October 2026).
- Assign `likely_bed_occupancy` once with a reproducible seeded Bernoulli draw using explicitly fictional category probabilities. A true flag ALSO gives higher queue priority under the agreed demo assumption. This is not a clinical equivalence, an actual triage record, or an estimate from real urgency data. There is no separate urgency field.
- Keep that population, flags, staff rosters and bed capacities identical across all five runs. Vary only clinician service-duration draws by run. Each patient's duration draws are seeded by patient ID, allowing later resource comparisons to reuse the same work.
- Run each hospital separately, continuously across all 28 days. Do not reset queues each day or generate a new population per run.

## Resource model

Source doctors and bed counts are interpreted as total available shift capacity for this simulation, not already-free resources. Free resources are calculated from ongoing work. Shift changes update capacity; ongoing work is never interrupted if the new shift has less capacity.

A patient starts general-doctor contact when a doctor is free and, for a bed-flagged patient, a treatment space is free. Priority cases overtake waiting standard cases, without interrupting care in progress. A blocked patient needing a space does not prevent another patient who can be served from starting.

After general assessment, patients with a mapped specialty wait for specialist review. The general doctor becomes free; the treatment space remains occupied for bed-flagged cases until specialist review finishes. Consequently specialists can affect first-doctor waits indirectly through occupied spaces. Specialists are not mandatory for initial general-doctor contact.

General and specialist service times follow lognormal distributions with coefficient of variation 0.35, minimum one minute. Per-category mean service durations and flag probabilities are recorded explicitly in output metadata. They are toy assumptions, not NHS measurements. Doctors on shift are an input; service time determines throughput and how long they stay busy.

Queues start empty at the beginning of the source period, with no warm-up. At the end, stop arrivals but continue treating the remaining queue using the final shift's capacity. Report the last completion per run. These boundary assumptions can affect the earliest and latest records.

Priority is treated as known at arrival; a separate triage duration is not simulated. This flag must not become an assumed input to pre-triage patient recommendations.

## Outputs

Each visit includes all five `simulation_waits_minutes`, their mean/min/max/sample standard deviation and `mean_first_doctor_at`. Each patient mean is rounded UP once after averaging the five unrounded samples and stored as an integer (`ceil(mean(samples))`). Min/max and sample standard deviation remain unrounded; the ceiled mean may slightly exceed the maximum raw sample. The mean timestamp is arrival plus that integer wait; it is not the observed timestamp from any particular run. There are only five replications, so their spread is not a calibrated confidence interval.

Generated visits omit repeated complaint labels, diagnosis durations and the former arrival-to-diagnosis total. Complaint IDs are retained for stable API/category mapping. Generated hospital records omit NHS source, A&E source and synthetic flag columns; the synthetic notice stays in dataset metadata.

Staffing outputs preserve resource inputs and append simulated mean free resources and queue sizes. Snapshot influx is `observed_arrivals_last_hour`, calculated from arrivals in `[snapshot_time - 1 hour, snapshot_time)`; it is never the count of future arrivals. At the first snapshot it is zero because there is no earlier source history. Daily priority-case expectations are sums of category flag probabilities; realised counts are fixed across runs because patients and flags are fixed.

## Completed run

Seed: `20261024`. All five runs completed all 42,000 patients: 210,000 patient-runs. Per-run overall mean waits were 23.56, 23.38, 24.02, 23.38 and 23.17 minutes. The unrounded mean across patients and runs was 23.501946 minutes. Following the integer-rounding update, the average of the 42,000 stored integer means is 23.785786 minutes; rounding did not change any simulation samples. The summary retains both rounded-output and unrounded overall means. Every patient's stored mean was checked against their five nonnegative finite samples; IDs, arrivals and category assignments were verified against the original source. All 840 snapshots were generated.

Outputs for this workspace are under `/workspace/outputs/queuecare-simulation/`, including an additional `patient_average_waits.csv` export for inspection. That CSV is a derivative of the completed JSON; the generator's primary outputs are JSON.

## Integration boundary

The live Supabase data is still the original dataset. This run is a separately generated artifact, not a live migration or a new API deployment. Do not send it through the old importer: first-doctor outputs have a different schema and meaning from the original referral records. Before replacing live records, preserve any database edits, apply a tested schema migration and update the importer together.

PR #1's `queuecare.v1` contract still specifies referral, its original historical means and `demo_baseline_scaling_v1`. A new model must not silently reinterpret those fields or change `estimateMethod` and fixtures without coordinating that contract update. Keep scenario state and first-doctor simulation distinct from the old model until integration is agreed.

## Why the initial wait estimates are low

The source fixes each hospital at 300 arrivals/day (12.5/hour). It supplies an average 17.714 general doctors, 19.977 specialists across all specialties, and 30.732 ED spaces per hospital/shift. The fictional general service-time mean weighted by this case mix is 60.250 minutes. Expected aggregate general-doctor utilisation is only 70.86% (required clinician-minutes divided by rostered clinician-minutes). Peak four-hour arrival rate is 27.75/hour, so some queues still form during surges.

At snapshot boundaries the simulation averaged 5.59 free general doctors and 25.08 free treatment spaces. 18,596 patients had zero wait in all five runs. Those outcomes follow from generous resource inputs, limited bed need, and perfect resource usability. There are no staff breaks, competing duties, triage-processing delays, diagnostics-blocked beds or inpatient admission blockage. The empty starting queue also affects early records. Referral/total-A&E metrics from outside this simulation are different from first-doctor waits and cannot calibrate it directly.

Do not tune inputs merely to force a dramatic target. A next sensitivity analysis can reduce effective doctor availability or increase arrivals while retaining and reporting the original baseline. No resource, arrival, or service-duration assumptions were changed by the integer-rounding update.
