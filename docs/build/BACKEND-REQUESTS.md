# What the frontend needs from the backend

**FRONTEND · 25 October 2026 · foundation PR #3, UI PR #4.** This is the frontend owner's exact request list for Zack's agent, written against the code that already exists on `ajjar/app-foundation` and `ajjar/patient-ui`. The owning contract stays [INTERFACES.md](../INTERFACES.md) and [contracts/queuecare.ts](../../contracts/queuecare.ts); if a shape must change, change those plus the fixtures together and say so on [issue #2](https://github.com/ajjarm/oxhack-project/issues/2). Nothing here is authorization to change scope.

## Where to build

- Branch from `ajjar/app-foundation` (PR #3), not `main`, into `zack/backend`. Declare the dependency in your PR.
- Your files: `src/app/api/**`, `src/lib/server/**`, `supabase/**` (migrations, seed), `package.json` + `package-lock.json`, `.env.example` additions. Do not edit `src/components/**`, `src/app/page.tsx`, `src/app/patient/**`, `src/app/hospital/**` or `src/lib/api/**` (the client); ask on issue #2 if you need something there.
- Run: `npm ci`, then `NEXT_PUBLIC_DATA_MODE=live npm run dev`. In live mode every screen calls your routes and shows a `NOT_CONNECTED` error card for any route that does not exist yet; nothing falls back to samples. `npm run check` must stay green.

## The exact HTTP calls the UI makes

The live adapter is [src/lib/api/live.ts](../../src/lib/api/live.ts). It sends `accept: application/json`, JSON bodies with `content-type: application/json`, and parses any non-2xx body as the contract `ErrorResponse` (`{ schemaVersion, error: { code, message, currentStateVersion? } }`). An HTML or empty error body is shown as `INTERNAL_ERROR` with the status.

| # | Call | Request | Success | Status |
| --- | --- | --- | --- | --- |
| 1 | `GET /api/catalog` | none | `CatalogResponse` ([fixture](../../fixtures/queuecare/catalog.response.json)) | contract |
| 2 | `POST /api/compare` | `CompareRequest` ([fixture](../../fixtures/queuecare/compare.request.json)) | `CompareResponse`, server order preserved, unrankable rows after ranked ones | contract |
| 3 | `GET /api/scenarios/{scenarioId}/dashboard?simulationAt=<URL-encoded ISO>` | query | `DashboardResponse` | contract |
| 4 | `PATCH /api/scenarios/{scenarioId}/hospitals/{hospitalId}/capacity` | `CapacityRequest` with `expectedStateVersion` | full `DashboardResponse` at the new version; `409 STATE_CONFLICT` with `currentStateVersion` when stale | contract |
| 5 | `POST /api/classify` | multipart form: `symptoms` (string, optional), `image` (file, optional; JPEG/PNG/WebP ≤ 3 MiB); at least one | `{ "suggestedCategory": <catalog id or null>, "requiresConfirmation": true, "source": "gemini" \| "none", "message"?: string }` | proposed |
| 6 | `POST /api/scenarios/{scenarioId}/events` | `{ "kind": "destination_selected", "hospitalId", "complaintCategory", "simulationAt", "estimatedArrivalAt": string \| null, "expectedStateVersion" }` | `DestinationIntention`: the input plus `intentionId`, `scenarioId`, `recordedAt`, `storage: "backend"`; `409` when the version is stale | proposed |
| 7 | `GET /api/scenarios/{scenarioId}/intentions` | none | `DestinationIntention[]` for the scenario, oldest first | proposed |

Types for 5–7 are in [src/lib/api/proposed.ts](../../src/lib/api/proposed.ts). Promote them into `contracts/queuecare.ts` when you implement them, or reply with the shape you prefer and the frontend adapts the client.

Order that unblocks the demo: 1 → 2 and 3 → 4 → 5 → 6 and 7 → forecast route from [MODELS-AND-DATA.md](MODELS-AND-DATA.md#backend-changes-to-agree). The UI has no forecast screen bound yet; publish the forecast shape before implementing it and the frontend will bind the Demand forecasting tab.

## Rules the UI already relies on

- `null` means unavailable and renders as “—”; never send `0` for an unknown value.
- Timestamps carry an offset (`+01:00`); clocks are shown in Europe/London. The scenario clock is `simulationAt`, never the server's current time.
- `stateVersion` on every read; the dashboard and the comparison for the same scenario must report the same version.
- `suitability` values and `ErrorResponse` codes exactly as in the contract; `complaintCategory` is validated against the catalog enum (`other_or_uncategorised`, not `other_uncategorised`).
- Capacity writes need the agreed demo access control before the route is public; the UI sends no credentials today, so say what header or cookie you expect.
- Secrets stay server-side in `.env.local` and the Vercel project; the only `NEXT_PUBLIC_` variable is `NEXT_PUBLIC_DATA_MODE`.

## First acceptance check (SCOPE)

1. Live mode, `/patient`: describe → category fracture → Results shows five hospitals from your `/api/compare`.
2. `/hospital` → Staffing coordination → H001 general doctors 16 → 8 → Save succeeds, version increments.
3. `/patient` → Compare again: H001 wait 97 → 193, total 121 → 217, other hospitals unchanged, same version on both screens.
4. Second browser: refresh shows the saved change. Save again with the old version from the first browser → conflict banner.

Post `CATALOG_READY` (then `COMPARE_READY`, `CAPACITY_READY`, …) on issue #2 with the PR link, the real response and the commands you ran. The frontend reads the thread at its checkpoints and answers with `CATALOG_CONNECTED` once the first live read works.
