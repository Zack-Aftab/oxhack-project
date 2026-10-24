# QueueCare database

The live Supabase project has been migrated, loaded and verified: **5 hospitals, 68,705 visits and 3,600 hourly snapshots**. Every stored integer average and all five samples per patient were checked. Original data was backed up and archived. See [verification evidence](../simulation/results/month-v5/supabase-verification.json).

The selected dataset is now the **30-day, five-run simulation**, not the initial 42,000-visit source or the superseded weekly/monthly experiments.

See [simulation/README.md](../simulation/README.md) for reproduction, schema, backup, migration and import commands. The executable simulator, compact input, compressed selected dataset, summaries and tests live together in `simulation/`.

The initial Supabase schema was imported earlier. Its replacement migration is `supabase/migrations/202610240003_monthly_simulation.sql`. It preserves the original public tables in a private archive, creates the new schema, and retains row-level security. Do not rerun `001` or apply the superseded `002` label proposal to the existing project.

New visits retain `complaint_category` as the stable API category ID; they omit repeated display labels and diagnosis/total-stay durations. `mean_wait_to_first_doctor_minutes` is an integer ceiling of five samples. The bed flag is known at reception and gives priority at triage and general-doctor queues under the agreed demo rule. Staff snapshots contain prior-hour observed influx, not future arrivals. All data is synthetic.

Credentials belong only in secure environment settings or ignored `.env.local`: `SUPABASE_URL` and `SUPABASE_SECRET_KEY`. Never expose the key through `NEXT_PUBLIC_` or browser code. API response shapes remain subject to the shared PR #1 agreement; no backend response was silently changed by this migration.
