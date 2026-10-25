# BACKEND — live catalog connection

Implemented on `zack/backend`, based on unmerged `ajjar/app-foundation` commit `03c93f0e416835fe306a69cfbe42030c67dddb23` (PR #3). Read the FRONTEND / FOUNDATION_READY comment on issue #2 and `BACKEND-REQUESTS.md` before implementation. Existing database work is preserved; no database mutations or new frontend scaffold were made.

## Implemented and verified

`GET /api/catalog` returned HTTP **200**, `Content-Type: application/json`, `Cache-Control: no-store` from the actual Next.js Route Handler reading the existing Supabase project. The [captured response](examples/catalog.live.response.json) contains five hospitals (`H001`–`H005`), eight category IDs, the stored synthetic-data notice and actual inclusive date range **2026-09-21–2026-10-20**. It is evidence captured from a request, not a runtime fixture or fallback.

The route reads only:

- `hospitals`: `hospital_id` primary key, `name`, `address`, `latitude`, `longitude`.
- `simulation_datasets`: `dataset_id` primary key, `model_version`, `metadata` (and stored `summary`, `imported_at`, not needed by the route). Selected row: `month-v5`, model `resource_queue_month_v5`.

Category IDs come from keys in `metadata.category_specific_flag_probabilities`, which were imported with the dataset. Their labels and `demoSpecialty` values are the agreed server-side display dictionary. No operational probability values or entire visit history reach the client. A database failure, missing category metadata, unknown ID or invalid record produces the contract `ErrorResponse` with HTTP 500 / `INTERNAL_ERROR`; there is no sample fallback or raw credential/provider error.

The `CatalogResponse` shape and existing `contracts/queuecare.ts` are unchanged. Default comparison remains `demo-1`, `2026-09-25T18:00:00+01:00`, fracture category and London demo travel. These are default request parameters; a catalog response does not claim a persisted scenario or implemented comparison route. `demoSpecialty` is a category hint, not confirmed hospital specialty coverage.

## Existing selected data

The monthly import was previously completed and verified: **5 hospitals, 68,705 visits, 3,600 hourly staffing snapshots**, and one dataset metadata row. Original data (5 / 42,000 / 840) remains backed up and archived in `queuecare_archive_20261024`. Current runtime catalog access verifies the hospitals and imported dataset metadata; it does not rescan every visit on every request.

Other existing tables/columns:

- `visits`: `visit_id` PK, `hospital_id` FK, `arrival_at`, `complaint_category`, `likely_bed_occupancy`, integer `mean_wait_to_first_doctor_minutes`, `mean_first_doctor_at`, five `simulation_waits_minutes`, run count, min/max/standard deviation.
- `staffing_snapshots`: `snapshot_id` PK, `hospital_id` FK, hourly start/end, effective general doctors, triage nurses, support-space capacity, previous-hour observed arrivals and mean free resources / queues.

Migrations `001` and `003` are preserved under `supabase/migrations` for inspection. Do not rerun them on the existing populated project. No Gemini pain/urgency migration is applied or required by this catalog change.

## Setup

Node.js 24, npm, existing foundation lockfile. No new runtime dependency is needed.

```sh
npm ci
# Add server-only values privately to .env.local or your runtime environment:
# SUPABASE_URL, SUPABASE_SECRET_KEY
# Legacy alternative: SUPABASE_SERVICE_ROLE_KEY (one key binding suffices)
# SUPABASE_DATASET_ID=month-v5
NODE_USE_ENV_PROXY=1 NEXT_PUBLIC_DATA_MODE=live npm run dev -- --port 3011
curl --fail --silent http://127.0.0.1:3011/api/catalog
node --test src/lib/server/catalog.test.mts
npm run check
```

`NODE_USE_ENV_PROXY=1` is needed in this cloud machine; local/Vercel environments without an egress proxy do not require it. Secrets must never use `NEXT_PUBLIC_`. The frontend's only public setting remains `NEXT_PUBLIC_DATA_MODE`.

## Foundation repair and checks

The supplied foundation included `comparison-view.test.mts` importing an absent `src/lib/comparison-view.ts`. Restored that exact existing helper from `ajjar/patient-ui` commit `d7de01c1a862402ebef0a4cf0f10ada0f555bfb2`; no frontend components, pages, styles or API client were edited. This avoids maintaining a second implementation and should agree byte-for-byte with the frontend branch when stacked PRs merge.

Five new backend tests cover live-row mapping, inclusive date conversion, missing/corrupt data with no fallback, REST headers/redirect/cache settings and credential/403 failures. The live route was also requested against Supabase rather than only mocked.

Executed checks: `npm run lint` passed; `npm run typecheck` passed; `npm run test` passed **12 tests**. `npm run check` reached the production build, which is currently blocked by the cloud network denying the existing Inter Google Font request. This is an environment prerequisite, not a passing build. GitHub publishing details are completed in the PR/handoff after access is available. The build needs `fonts.googleapis.com` / `fonts.gstatic.com`; GitHub PR/comment publishing needs `api.github.com`. Network HTTP 403 blocks are distinct from database readiness and repository Git access.

## Follow-on contract work (not implemented here)

Compare, dashboard, capacity writes, Gemini intake, intentions and forecasting remain follow-on routes. The current database's first-general-doctor waits are **not** the original referral/diagnosis events. Its snapshots are hourly, not four-hour; general-doctor counts are the constrained simulation roster, not the old fixture's 16→8 example. No diagnosis totals or specialist availability are manufactured to fill the old response fields. Reconcile those differences with the frontend/data owners, updating types/docs/fixtures together before implementing the next model. Catalog only is ready for its first live read; the complete old SCOPE comparison loop is not claimed.
