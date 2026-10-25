# Backend connection handoff — BLOCKED

Checked 25 October 2026. This is an evidence report, not a database implementation or a readiness announcement.

## Repository and ownership

Repository: https://github.com/ajjarm/oxhack-project

Context: PR #1, `ajjar/queuecare-contract`, still unmerged when inspected. Intended task branch: `zack/database-handoff`; creation failed with GitHub HTTP 403, `Resource not accessible by integration`. No branch, pushed commit or backend PR was created. Local task folder: `/workspace/scratch/b4d2fdcbf9de/backend-handoff-task` (not a Git checkout).

Read: AGENTS.md, README.md, docs/PROJECT.md, docs/SETUP.md, docs/build/ZACK-START-PROMPT.md, START-HERE.md, BUILD-PLAN.md, MODELS-AND-DATA.md, docs/INTERFACES.md, contracts/queuecare.ts and dataset review. Existing fixtures were inspected earlier in this session.

Claude owns the single Next.js foundation and both frontends. No new application scaffold, frontend or replacement database was created. Part B must use Claude's exact FOUNDATION_READY PR after its link is supplied.

## Existing database — unknown, not modified

The user reports existing Supabase work. No database connection, schema export, migration, import script or accessible SQL was found in the scoped working files. No Supabase connector is available. This session cannot inspect the user's WSL files or Supabase project through its separate scratch filesystem.

Actual tables, columns, SQL types, PK/FK constraints, indexes, RLS policies, project configuration and migration history: **unknown**. Imported database row counts: **not verified**. No live database query or migration ran; no shared database was reset or changed.

Source JSON collections previously inspected are `hospitals`, `visits`, `staffing_snapshots` and `dataset_metadata`. They do not establish the actual SQL schema. Dataset metadata declares five hospitals, 42,000 visits and 840 staffing snapshots. These are NOT verified imported row counts. Source hospital identifiers are H001–H005 and catalog category IDs are preserved by the contract.

No actual SQL can be published from this environment until the existing schema/migrations are supplied. Obtain a schema-only export without secrets, SQL editor migration files, and non-sensitive count-query results; do not send a password, privileged key or real environment file. Inspect and reconcile those artifacts before designing any additional migration. Actual import/run instructions remain unavailable because the existing schema and import method are unknown.

## HTTP endpoints

**Core API not implemented in inspected work; database readiness unverified.**

The requested phrase "Database ready; API not implemented." is conditional on a ready database. It is not a verified status here and must not be used as a readiness signal.

| Route | Status |
| --- | --- |
| GET /api/catalog | Accepted contract; no implemented handler or tested response |
| POST /api/compare | Accepted contract; no implemented handler or tested response |
| GET /api/scenarios/{scenarioId}/dashboard?simulationAt=... | Accepted contract; no implemented handler or tested response |
| PATCH /api/scenarios/{scenarioId}/hospitals/{hospitalId}/capacity | Accepted contract; no implemented handler or tested response |

There are no working core HTTP request/response examples to report. The examples in fixtures/queuecare are sample contracts, not responses captured from running routes.

## Existing backend reference code

`inputs/backend/classifier-prototype.mjs` is a copy of the locally written Express classifier experiment. It is archived backend reference code, not the chosen app foundation or an active application service. No frontend, package manifest, environment file or dependency tree accompanies it here. Preserve the main Next.js architecture and port appropriate logic only after the foundation is supplied.

Verification: `node --check docs/build/inputs/backend/classifier-prototype.mjs` passed in the local task directory. This checks syntax only, not dependencies, Gemini or HTTP behavior. The user's earlier local screenshot showed an upload UI and provider status 404; a successful Gemini classification remains unverified. The original experiment's working directory had `node server.mjs` as its run command; the archived reference is not the shared application's run target.

Written prototype route: POST /classify, multipart binary field `image`, MIME JPEG/PNG/WebP, limit 3 MiB. No caller authentication. MIME validation is not image-byte decoding. Written success example (not captured output):

```json
{"category":"cuts_or_wounds"}
```

Written HTTP 502 error example (not captured output):

```json
{"error":"Gemini request failed. Check your API key and model availability."}
```

Differences from the intended Next.js classifier extension: `/classify` rather than `/api/classify`; image-only rather than optional image plus description; `{category}` rather than `{suggestedCategory, requiresConfirmation: true}`; legacy error envelope; no user-confirmation persistence or validated file decoding. Its category strings use catalog-compatible IDs, including `other_or_uncategorised`. Do not point the shared frontend at this archived experiment.

Environment names used by that prototype only: `GEMINI_API_KEY`, `GEMINI_MODEL`. Actual Supabase environment names and app setup/run commands are **unknown** until existing configuration and Claude's foundation are inspected. No backend URL is verified live.

## Initial agreement and follow-on tasks

The four-route request/success shapes in docs/INTERFACES.md are accepted as the first integration checkpoint, not implemented functionality. Retain the September fixture clock `2026-09-25T18:00:00+01:00`, explicit demo travel H001=24/H002=18/H003=12/H004=20/H005=32 minutes, and `demo_baseline_scaling_v1` for that checkpoint. Never call it a past-only forecast. Source data and immutable history must not be restructured solely to match camelCase response objects.

Planned shared state: Supabase scenario/version records and absolute overrides keyed by (scenarioId, snapshotId), with atomic optimistic version checks and consistent reads. No tables/functions implementing this were inspected. Both screens must use the same database/scenario; refresh/recompare initially, no implicit synchronization through fixtures or browser localStorage.

Proposed access addition, not yet edited into shared types: capacity writes require a server-validated session and scenario-editor authorization; add HTTP 401 UNAUTHENTICATED and HTTP 403 FORBIDDEN in the existing error envelope. No privileged browser credentials. Public demo reads may stay available. Reconcile and update owning docs/types/fixtures before implementing access changes.

The expanded plan's forecast clock `2026-10-12T08:00:00+01:00`, past-only model, common queue/ranking engine, events and forecast/classifier interfaces are subsequent work. That clock is not silently substituted into v1 fixtures. Model integration and exact shape changes remain unimplemented. Use the third teammate's model work where available; do not duplicate their forecasting engine.

## Blocking handoff requirements

1. GitHub integration write access: branch creation returned HTTP 403. Reading succeeds; publication does not. No alternate account was used to bypass that failure.
2. Existing Supabase schema/SQL/import evidence or supported access: none is available to this environment. Database readiness cannot be asserted without it.
3. Claude's exact foundation PR link: not yet supplied. CATALOG_READY requires actual Supabase-to-HTTP proof on that foundation.

DATABASE_HANDOFF_READY and CATALOG_READY have NOT been achieved. No PR link, verified import count, tested endpoint or successful application run is invented by this document.
