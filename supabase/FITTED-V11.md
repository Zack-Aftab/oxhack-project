# Activate the fitted demo dataset

Status: **applied and independently verified live on 25 October 2026**. The management API ran the small setup, all67,676 records were uploaded in batches, and the service-only activation RPC switched the active dataset to fitted-v11. Live SQL and REST verification passed. See [verification/fitted-v11-live.json](verification/fitted-v11-live.json). Prior68,705 visits and3,600 staffing rows remain in the private backup schema.

Run the complete generated `downloads/APPLY_FITTED_V11.sql` in the existing project's SQL Editor. The script imports all data, validates it, archives prior tables in the private `queuecare_before_fitted_v11` schema, and activates the new public views in one transaction. Re-running the full script is safe. Do not rerun old migrations001/003.

The final SQL results must show:

- Active dataset `fitted-v11`.
- 67,473 hospital visits; 203 emergency exits in `demo_visit_results`.
- Continuous fitted mean120 and median100; stored integer mean120.50.
- Bands: 3374 /3373 /15069 /19425 /15028 /11204 patients.
- 35 explicit hospital/specialty cells, 3,600 hourly capacity records, 25,200 hourly specialist staffing records.

`public.visits` becomes a view over the active fitted dataset. It includes all confirmed categories, derived required specialties, pain, synthetic urgency, the bed flag, raw event-queue waits and separately named fitted demo waits. `mean_wait_to_first_doctor_minutes` remains a compatibility alias for the integer fitted estimate. `complaint_category` remains a compatibility projection of the first category; multi-category eligibility must use the full array. These estimates are not a five-run average or observed clinical outcomes.

`public.staffing_snapshots` becomes the active capacity view; on-duty doctors and total support-bed capacity are labelled explicitly. Unrecorded free-resource/queue telemetry isNULL. Previous-hour influx is calculated from actual simulated arrival records; first-hour influx isNULL because warmup rows are not imported. `public.hospital_influx` provides per-hospital simulation-date arrival counts. `public.specialist_staffing` exposes active hourly specialty capacity. Unknown complaints remain manual-selection cases; specialty support is never unknown.

Old visits and staffing remain intact in the private archive. Existing dataset metadata rows remain under their original IDs. Row-level security and service-role-only reads are retained. Emergency exits have no hospital or wait and do not appear among hospital visits.

The ZIP `downloads/supabase-fitted-v11.zip` contains the full script, verification queries, and a smaller three-step fallback if SQL Editor rejects the file size: prepareSQL, import the numeric CSV into `demo_fitted_v11_import` using Table Editor, then activateSQL. Activation refuses incomplete or mismatched data. Staging data does not become active until validation succeeds.

Backend configuration after activation should select `SUPABASE_DATASET_ID=fitted-v11`; the opt-in multi reader currently defaults to specialist-v7 and needs its dataset ID changed to fitted-v11 before that route uses the new estimates. No API response shape was changed by this database-only task. The raw simulation and fixed fitted transformation remain reproducible in the simulation folder.

Regenerate the files with:

```sh
python3 simulation/export_supabase_v11.py /tmp/new-v11-sql-export
```

Local PostgreSQL-compatible PGlite verification applied the full script twice against the existing monthly schema, including old sample visits/staffing, and checked row counts, targets, representative patient values, category coverage, preserved backups, service-role reads and denied anonymous reads. No live mutation has been claimed.

## Small setup plus automated batch upload

If the full query is too large, run `downloads/SUPABASE_SMALL_SETUP.sql` (about46KB) in SQL Editor, and replace the existing `SUPABASE_SECRET_KEY` value securely in this Codex environment's Secrets settings. It must be a server-side Supabase Secret key for this project. No key belongs in chat or GitHub.

The small setup installs the same staging/capacity data and a parameterless activation RPC. That RPC is callable only by service_role, contains no arbitrary SQL input, validates the entire fixed v11 dataset and preserves the previous tables before switching views. Incomplete uploads cannot activate. It was tested locally as service_role, including repeated activation and denied anonymous calls.

Then the assistant can run:

```sh
NODE_USE_ENV_PROXY=1 node simulation/import_fitted_v11.mjs --apply
```

The importer upserts 1,000 records per HTTP request and calls the validated activation function only after all batches succeed. It retains epoch microseconds as decimal strings to avoid JavaScript integer precision loss. `--dry-run` prepares records without making any network request. The import and activation have now been completed; file generation alone does not perform an update.
