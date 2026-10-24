# Proposed frontend–backend agreement

**Version: `queuecare.v1` · 24 October 2026**

You can build the UI now using [the sample responses](../fixtures/queuecare/README.md). This is a proposal awaiting backend-owner agreement. Once accepted, both sides use these fields. The database can keep the source file's snake_case columns; the API translates them into the camelCase types in [contracts/queuecare.ts](../contracts/queuecare.ts).

The [backend handoff](build/inputs/BACKEND-HANDOFF.md) could not inspect this proposal and verifies no core API or database. It does not establish a competing core contract. Give the backend owner this file and reconcile any newer code before connecting the UI. Change the documentation, types and affected fixtures together if the agreement changes. The toy model below is an assistant-authored demo option, not a validated predictor or an algorithm the teammate has already adopted. The database import does not need restructuring to match response objects. The app is unnamed; `queuecare.v1` is a temporary schema identifier.

**Expanded build, 25 October:** this four-route model is the first integration checkpoint. [BUILD-PLAN.md](build/BUILD-PLAN.md) requires subsequent Gemini intake, a shared time-dependent ranking/queue engine and evaluated forecasting. [MODELS-AND-DATA.md](build/MODELS-AND-DATA.md#backend-changes-to-agree) lists the proposed extensions. Those are not yet part of these wire types; agree changes and update this file/types/fixtures before implementing them. The current full-history toy fixtures are not past-only forecast-validation evidence.

## One instruction for each coding assistant

> Read docs/build/START-HERE.md, docs/INTERFACES.md, contracts/queuecare.ts and fixtures/queuecare/README.md. Use the proposal consistently for fixture UI work. Confirm or reconcile it with the backend owner before connected integration. After agreement, the backend maps the dataset into that contract and validates requests at runtime. Record a needed contract change before implementing a conflicting shape.

Implementation target: React through Next.js App Router, TypeScript and Tailwind; API routes in the same Next.js app; Supabase Postgres for shared scenario state; npm and Node.js 24 LTS; Vercel deployment. Nothing here scaffolds or configures those services.

## The input we actually have

- 5 hospitals, IDs `H001`–`H005`; 42,000 synthetic visits; 840 four-hour staffing snapshots.
- Simulation dates: **2026-09-21 through 2026-10-18**, Europe/London. Start the demo at **2026-09-25T18:00:00+01:00**, not the computer's current time.
- Real hospital names and locations; invented operational values. Display the returned `notice` on both screens.
- No travel durations, urgency scores, live feed, measured service rates or demand forecast. See the [short dataset review](DATASET-REVIEW.md).
- The original 23 MB input remains external. The fixture manifest records its SHA-256 so the importer can confirm it has the same file.

## Four connections to build

| Method and URL | Input | Success response / example |
| --- | --- | --- |
| `GET /api/catalog` | None | `CatalogResponse`; [catalog](../fixtures/queuecare/catalog.response.json) |
| `POST /api/compare` | `CompareRequest`; [example](../fixtures/queuecare/compare.request.json) | `CompareResponse`; [baseline](../fixtures/queuecare/compare.response.json) |
| `GET /api/scenarios/{scenarioId}/dashboard?simulationAt=...` | Offset-aware ISO timestamp; encode it with `URLSearchParams` | `DashboardResponse`; [baseline](../fixtures/queuecare/dashboard.response.json) |
| `PATCH /api/scenarios/{scenarioId}/hospitals/{hospitalId}/capacity` | `CapacityRequest`; [example](../fixtures/queuecare/capacity.request.json) | Full updated `DashboardResponse`; [changed state](../fixtures/queuecare/dashboard.capacity-changed.response.json) |

Successful responses use HTTP 200 and JSON. The first named scenario is `demo-1`, initialized from the dataset, with `stateVersion: 0`. Comparing or reading a dashboard must not add a patient or mutate state.

## Patient screen: request and display

Load form options from the catalog. Send the exact complaint-category ID; do not send the visible label or invent a clinical urgency value. The server derives the demo specialty from the category mapping in the dataset.

Example comparison request:

```json
{
  "scenarioId": "demo-1",
  "simulationAt": "2026-09-25T18:00:00+01:00",
  "complaintCategory": "fracture_sprain_or_dislocation",
  "originId": "london-demo",
  "travelMode": "demo"
}
```

The response contains `hospitals`, not the entire visits table. Render a card per returned hospital using `hospitalId` as the key. Read the full shape from the shared types and fixture rather than copying an earlier chat's provisional `facilityId` or `caseId` examples.

| Field | Exact meaning / UI label |
| --- | --- |
| `suitability` | `demo_match`, `demo_unavailable`, or `unknown`. This is a simulated resource match, not confirmed clinical suitability. |
| `travelMinutes` | Added illustrative journey duration, or `null`. Label **Demo travel** while `travelSource` is `demo_fixture`. |
| `estimatedArrivalAt` | `simulationAt` plus travel; `null` without travel. |
| `predictedWaitToReferralOnArrivalMinutes` | Demo-model estimate from arrival to doctor referral. Label **Simulated wait to referral**. |
| `totalToReferralMinutes` | Travel plus that wait, excluding referral-to-diagnosis. Label **Demo travel + wait to referral**. |
| `historicalBaseline.meanWaitToReferralMinutes` | Retrospective synthetic mean from reception to doctor referral. |
| `historicalBaseline.meanReferralToDiagnosisMinutes` | Separate retrospective mean from referral to diagnosis. |
| `historicalBaseline.meanArrivalToDiagnosisMinutes` | Sum of the two source intervals; excludes travel. |
| `historicalBaseline.sampleCount` | Number of source visits contributing to this baseline. |

Do not label referral as completed treatment, discharge, or a verified time at which a patient was seen by a doctor. The source records referral and diagnosis timestamps, not a separate doctor-seen event.

All durations are nonnegative numbers in minutes. Counts are nonnegative integers. IDs are strings. Timestamps include a timezone offset. `null` means unavailable; zero means an actual zero. Historical means can have decimals; round only for presentation.

Only matching rows with known totals are sorted by ascending `totalToReferralMinutes`; unrankable rows follow, ordered by hospital ID. Do not call an unrankable row the fastest option. An unknown complaint category returns `suitability: "unknown"` and no predicted wait or total.

## Travel is a separate dependency

`travelMode: "demo"` accepts only `originId: "london-demo"` and uses the explicit invented values in [manifest.json](../fixtures/queuecare/manifest.json). They are not calculated from real locations or supplied by a maps API.

`travelMode: "unavailable"` returns `travelSource: "not_configured"`; all journey, arrival-time, predicted-on-arrival and total fields are `null`. It can still return the current-window historical baseline and simulated resource status.

Real GPS/routing is not implemented or implied by v1. Add a separately agreed routing input and provenance before presenting real journey estimates. Never silently turn a missing route into a zero-minute journey.

## Small, reproducible demo calculation

The fixture generator provides **`demo_baseline_scaling_v1`**, a toy illustration, not a validated queue forecast. The backend should reproduce this model for the first integration; a later model change must update `estimateMethod` and the fixtures together.

1. Compute estimated arrival from the explicit demo journey.
2. Select the staffing snapshot containing that arrival: `snapshot_at <= arrival < staffing_window_end`.
3. Take the source visits for that hospital, complaint category, weekday and four-hour arrival bucket across the full supplied four-week dataset. Their mean referral wait is the baseline. This is retrospective analysis of synthetic data, not a chronological forecasting/backtest result.
4. Apply only the general-doctor scenario multiplier:
   `predictedWait = ceil(baselineMean * snapshotGeneralDoctors / effectiveGeneralDoctors)`.
5. Add travel to get `totalToReferralMinutes`. Do not add the diagnosis interval.

For a known complaint, a demo resource match requires a positive effective general-doctor count and a positive required-specialty count. `emergency_medicine` is represented by `general_doctors_available`; it is deliberately absent from the specialist map. Other missing specialty keys mean unknown, not zero or confirmed availability.

If the baseline has no samples or its source general-doctor count is zero, return unavailable means/estimates as appropriate, never divide by zero. With zero effective general doctors or zero required specialists, return `demo_unavailable` and no predicted wait or total. `unknown` complaints stay unknown even if general doctors exist.

Bed counts and specialist counts are displayed, but this first model does not predict their effect on delay. Do not claim changing an unmodelled resource improved the wait. The first editable control is **general doctors** only.

## Hospital dashboard and capacity changes

Use the same hospital IDs, `scenarioId`, simulation time and `stateVersion` as the patient comparison. Each dashboard row includes the selected snapshot window, effective and baseline general-doctor counts, specialist counts, ED treatment-space count, both queue counts, category-specific historical wait baselines and historical arrivals in the window.

Source mapping:

| Source/database | API |
| --- | --- |
| `hospital_id` | `hospitalId` |
| `snapshot_id`, `snapshot_at`, `staffing_window_end` | `snapshotId`, `windowStart`, `windowEnd` |
| `general_doctors_available` | `baselineGeneralDoctorsAvailable`; `generalDoctorsAvailable` includes a scenario override |
| `specialty_doctors_available` | `specialtyDoctorsAvailable` |
| `beds_available` | `bedsAvailable` — ED spaces, not inpatient beds |
| `patients_waiting_for_doctor_referral` | `waitingForReferral` |
| `patients_waiting_for_diagnosis` | `waitingForDiagnosis` |
| `arrivals_during_next_4h` | `historicalArrivalsInWindow` — observed within this generated history, not predicted arrivals |
| `simulated_staffing_status` | `baselineStaffingStatus` — original synthetic label, not a recalculated quality rating |

A capacity PATCH sets an **absolute** general-doctor count for the hospital's snapshot containing `simulationAt`. Store overrides by `(scenarioId, snapshotId)`. Do not overwrite source history. It applies only to that four-hour window; future-window changes require a separate request.

Validate `expectedStateVersion` and save the change plus incremented scenario version atomically. Return HTTP 409 on a stale version with `currentStateVersion`. Reads/comparisons return the version they actually used. The changed dashboard and comparison examples use version 1; they change H001's selected window from 16 general doctors to 8, leaving all other hospitals unchanged.

After Save, refresh the dashboard and rerun the last comparison. In another tab/device, Compare or refresh again. Automatic polling and real-time subscriptions can follow later. Both screens must point to the same backend/database scenario for shared changes to appear.

## Error agreement

Return `ErrorResponse` from the shared types, never raw database errors:

- HTTP 422 `INVALID_REQUEST`: bad types, unknown category enum, unsupported demo origin/travel mode, negative/noninteger counts, malformed or timezone-free timestamp.
- HTTP 422 `SIMULATION_TIME_UNAVAILABLE`: requested time or arrival has no source staffing window. Do not silently use today's time or an unrelated latest snapshot.
- HTTP 404 `UNKNOWN_RESOURCE`: unknown scenario or hospital.
- HTTP 409 `STATE_CONFLICT`: another update advanced the scenario version; refresh before retrying.
- HTTP 500 `INTERNAL_ERROR`: unexpected failure; show a retry state.

## Working in parallel

- **UI owner:** components and one `api-client` adapter. Sample mode returns these JSON responses; connected mode calls these endpoints. Do not import the 42,000 visits into browser components or calculate the ranking independently.
- **Database/backend owner:** confirm or revise this proposal, then import the supplied file using its IDs, preserve both wait stages and timestamps, implement the agreed responses, validate input and store scenario changes separately. Keep Supabase secrets server-side. No database rename is required merely because the API uses camelCase.
- **Data/integration owner:** preserve the original input, verify its checksum, maintain the fixtures and exercise the baseline/changed/no-travel/unknown/zero-doctor cases. The external source file is not included in this PR.

Keep mock mode explicit. Do not silently return fixtures after a live request fails. Everyone needs the same accepted contract; the backend developer does not need to author it, but must know and agree to it.

## First acceptance check

1. Show all five fixture hospitals and both wait-stage labels on the relevant screens.
2. Compare the default fracture-category scenario through the API.
3. Change H001's general doctors from 16 to 8 and compare again using the same scenario.
4. Its example wait changes from **97 to 193 minutes** and its travel-plus-referral total from **121 to 217**. Other hospital estimates stay unchanged. These numbers demonstrate the explicit toy rule, not real hospital behavior.
5. Verify the unavailable-travel, unknown-complaint, zero-general-doctor and stale-version UI states.

Fixtures and TypeScript declarations are ready; HTTP routes, database import/migrations and the app remain to be implemented.
