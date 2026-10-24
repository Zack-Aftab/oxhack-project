# Selected QueueCare simulation

The selected model is `resource_queue_month_v5`: **30 measured days, three warm-up days, five runs of the same patient cohort**. It models reception to first general A&E doctor. All operations, probabilities and resource counts are synthetic assumptions, not verified hospital performance.

## Reproduce

Python 3.11+ standard library only; no pip install:

```sh
python3 simulation/run.py simulation/input.json /tmp/queuecare-new-run
python3 -m unittest discover -s simulation/tests -p 'test*.py' -v
```

The output directory must not already exist. Defaults: seed `20261025`, measured period 21 September–20 October 2026, warm-up 18–20 September. `--days 7` reproduces the earlier weekly experiment. Arrivals, complaint category and bed flags remain fixed across five runs; positive service and holding durations vary by run. Each saved patient wait is `ceil(mean(five raw waits))`, an integer.

`input.json` contains only the original synthetic case counts, specialty mappings and five hospital locations. It replaces the large original attendance file as the reproducible input. Its original-file checksum records provenance. No original wait times are reused.

## Rule and capacity assumptions

- About 5% need prolonged bed-supported care. The flag is known at reception and gives nonpreemptive priority at triage and general-doctor queues. This is a demo rule, not a clinical triage classification.
- All patients complete a general-doctor assessment before leaving. Doctors share one queue system; none are permanently reserved for flagged cases.
- Expected 450 arrivals/site/day, with daily variation and six four-hour arrival shares: 8%, 6%, 20%, 24%, 26%, 16%.
- Effective general doctors by those windows: **3, 3, 8, 10, 9, 6** (mean 6.5). General-doctor work averages twenty minutes, varying by case category. This deliberately constrains doctor throughput.
- Triage nurses: 2, 2, 3, 3, 3, 2; mean triage service 4.5 minutes.
- Twenty support spaces; flagged cases occupy one for an assumed twelve hours on average. This is not a model of actual inpatient admissions or recovery length. Nonflagged assessment spaces are not constrained.
- No artificial minimum wait. Specialists and transfers are outside this first-general-doctor model; no site capability or specialist staffing is asserted.
- See `engine.py` for distributions and queue events and `run.py` for the selected parameters. `archive/` retains superseded experiments.

## Selected results

`results/month-v5/` contains the reproducible compressed dataset, summary, extra-doctor control and validation evidence. There are **68,705 visits, 3,600 hourly snapshots and five hospitals**. Five measured runs total **343,525 patient-runs**. Bed flag share: approximately 4.99%.

Individual-wait mean: **192.81 minutes**; median: **111.92 minutes**. Across the stored, ceiled five-run patient averages, mean: **193.31 minutes**, median: **116 minutes**. Means and medians of those two distributions are different. These describe a designed congested scenario, not measured NHS performance.

## Supabase migration and import

**Current demo status:** the migration has been applied and the monthly dataset has been imported and verified. See `results/month-v5/supabase-verification.json`. Do not rerun the migration on this project; use import/verification commands to refresh or check the selected data. The migration steps below document setup for a legacy-schema project.

Node.js 24; no npm packages required. Use server-only environment variables `SUPABASE_URL` and `SUPABASE_SECRET_KEY` (see root `.env.example`). Never commit secrets. Node needs `NODE_USE_ENV_PROXY=1` in the cloud workspace.

1. Back up the existing four demo tables (write to a secure location outside Git):

   ```sh
   NODE_USE_ENV_PROXY=1 node --env-file-if-exists=.env.local simulation/database.mjs --backup /tmp/queuecare-before-migration.json
   ```

2. In Supabase SQL Editor, run **only** `supabase/migrations/202610240003_monthly_simulation.sql` on the existing demo project. The migration preserves original tables, rows and foreign keys in `queuecare_archive_20261024`. It creates empty replacement public tables with RLS enabled. It is transactional and intended to run once. It does not delete archived data. It does not depend on the unused label proposal `002`.

3. Import and verify the selected dataset:

   ```sh
   node simulation/database.mjs --validate simulation/results/month-v5/dataset.json.gz
   NODE_USE_ENV_PROXY=1 node --env-file-if-exists=.env.local simulation/database.mjs --import simulation/results/month-v5/dataset.json.gz --summary simulation/results/month-v5/summary.json
   ```

The import validates every record before writes, refuses unrelated existing IDs, batches upserts and checks exact counts plus sample averages/arrays. Raw sample comparisons allow only a 1e-9 minute tolerance for PostgREST JSON rounding; integer averages and flags are checked exactly. To verify every stored visit and finish metadata registration after an interrupted final check, use:

```sh
NODE_USE_ENV_PROXY=1 node --env-file-if-exists=.env.local simulation/database.mjs --verify simulation/results/month-v5/dataset.json.gz --summary simulation/results/month-v5/summary.json
```

A failed import can leave partial new rows; rerun the same command after fixing the failure. The old data remains archived. Metadata is written to `simulation_datasets` only after table counts and samples verify.

## Schema and integration boundary

- `hospitals`: ID, name, address, coordinates. Removed source URLs, synthetic flag and unused load profiles.
- `visits`: stable complaint-category ID (kept for API mapping), known bed flag, integer mean wait, mean contact timestamp, five raw samples and spread. Removed repeated category labels, old referral/diagnosis intervals and arrival-to-diagnosis total.
- `staffing_snapshots`: hourly staffing/support capacity, measured prior-hour influx, averaged free resources and queues. No invented specialist coverage or future influx.
- `simulation_datasets`: model version, synthetic notice, assumptions and aggregate results.
- The former `simulation_scenarios` table is preserved in the archive; it is not silently repurposed to a new API state shape.

The shared PR #1 wire contract is unchanged. It describes a referral model and needs coordinated backend mapping/model agreement before these first-doctor results can power it. No new HTTP responses or endpoints are claimed by this database task.

For a fresh database, first run `001_queuecare.sql` and then `003_monthly_simulation.sql`; skip the unused `002` label proposal. Never rerun `001` against the populated project.
