# Product scope

## The idea and the first version

A patient uses a phone to compare simulated hospital options. A hospital user explores a staffing change and sees its effect on the **same** patient comparison. Build one responsive web app; a Swift/native app is outside the first milestone.

The selected stack is Next.js App Router, React, TypeScript and Tailwind; Next.js Route Handlers; Supabase Postgres; npm and Node.js 24 LTS; Vercel. This is a decision, not an installed scaffold. Pin compatible dependency versions and document real commands during setup. Do not introduce a separate Express service just because one appears in an experimental chat snippet.

The app has no product name. `queuecare` filenames and `queuecare.v1` currently identify the dataset/proposed schema; do not mass-rename them or invent a brand.

## Build these small journeys in order

| ID | User can… | Completion check |
| --- | --- | --- |
| P1 | Choose a demo complaint and starting point, then compare hospitals on a phone | All five fixture hospitals render from returned data, with match status, travel, simulated wait to referral and total. Form changes drive a request through one API client. |
| P2 | Understand missing data and request failures | Loading, validation, no-match/unavailable, unknown complaint, missing travel, and retry states work. Unknown values never display as zero. |
| H1 | View the same scenario on a hospital dashboard | Hospital IDs, simulation clock, scenario/version, queues and capacity correspond to patient data. Historical arrivals are labelled historical. |
| H2 | Change a hospital's general-doctor count and compare again | A saved server-side scenario override updates dashboard and comparison consistently; another browser sees it after refresh/Compare. Stale saves show a conflict and refresh option. |

Start with **P1 and P2 in explicit sample mode** using the exported patient designs. Connect the first real comparison as soon as available, before polishing all screens. Then build H1/H2 and test the combined loop. A working sample UI completes the UI milestone; it does not complete connected integration.

## What the UI means

- Use the exact category IDs, units, error shapes and identifiers in the proposed [contract](../INTERFACES.md), pending backend agreement. Never substitute a display label for an ID.
- Minutes are minutes; timestamps carry offsets; IDs are strings; `null` means unavailable. Preserve `H001`–`H005`.
- Show a visible synthetic-data notice. Travel fixtures are invented demo travel; waits use an illustrative model. These are not current hospital estimates.
- Referral is not proof a doctor has seen the patient. Travel plus wait to referral is separate from arrival-to-diagnosis time.
- The frontend displays the backend's estimates and ordering; it does not develop a second ranking formula.
- Category selection is sufficient for P1. If designs include voice, text, photos, maps, forecasts or scores beyond available APIs, record them as later integrations. Do not make decorative controls appear functional or fabricate their results.

The wider idea includes assisted intake, confirmed extracted information and richer hospital demand views. Optional image classification is specifically discussed in the backend report. Implement these after the first loop when time and real interfaces allow. A category suggestion requires user confirmation/change; it is not a diagnosis or clinical-priority score. Native apps, live feeds, real routing and advanced forecasting are outside the first loop. Intended destination is not a confirmed hospital arrival.

## How the pieces fit

```mermaid
flowchart LR
    P[Patient UI] --> C[One API client]
    H[Hospital UI] --> C
    C --> F[Explicit sample mode: committed fixtures]
    C --> A[Connected mode: Next.js API routes]
    A --> D[Supabase: source data and shared scenarios]
```

Components use one typed client, suggested location `src/lib/api-client.ts`. Sample mode returns fixtures; connected mode calls same-origin `/api/...`. Use an explicit mode setting; a failed real request must show an error rather than silently switching to samples. Keep raw visits, database access and credentials out of browser components.

Both API and UI normally run in the same Next.js app on each developer's computer. A teammate's `localhost` is their laptop, not yours. For a phone demo, use a reachable shared deployment or a deliberately configured local-network URL. Record actual commands/URLs in [SETUP.md](../SETUP.md) once the scaffold exists. Separate laptops sharing changes must use the same configured database/scenario; sample mode cannot prove synchronization.

## Who changes which files

These are proposed paths for the first scaffold, not existing folders. Inspect newer code before creating them.

| Owner | Files / responsibility |
| --- | --- |
| Frontend: user | Patient and later hospital pages/components, styling/assets, typed API client; e.g. `src/app/(patient)/`, `src/app/(hospital)/`, `src/components/`, `src/lib/api-client.ts` |
| Backend/database teammate | `src/app/api/`, `src/lib/server/`, Supabase schema/migrations/import and shared scenario state; optional classifier route later |
| Third teammate | Data verification, fixture maintenance and end-to-end checks; coordinate changes to `fixtures/`, `scripts/` and contract files |
| One named owner at a time | Root scaffold, package/lock files, layout/global CSS, environment examples, deployment/CI and contract changes |

Recommendation: the frontend owner makes the first minimal Next.js scaffold because patient work is starting now. Tell the backend owner before starting so they extend that scaffold rather than generating another app. If they already made one, reuse it. After the foundation is shared, everyone works on separate branches/folders in parallel. See [WORKING-TOGETHER.md](../WORKING-TOGETHER.md) for save, push, review and merge steps.

## First connected milestone

```mermaid
sequenceDiagram
    participant P as Patient
    participant A as API and shared scenario
    participant H as Hospital dashboard
    P->>A: Compare complaint in scenario demo-1
    A-->>P: Hospital estimates, stateVersion 0
    H->>A: Save H001 doctor count 16 to 8, expected version 0
    A-->>H: Updated dashboard, stateVersion 1
    P->>A: Compare again with same inputs
    A-->>P: Changed H001 estimate, stateVersion 1
```

If the proposed model is accepted, its fixture expectation is H001 wait **97 → 193 minutes**, total **121 → 217**; other hospitals stay unchanged. If the backend owner chooses a different documented model, update contract/model notes and fixtures before asserting those numbers. Do not call fixture switching an end-to-end backend test.

Test the loop in two browsers against the same scenario. Also check failed requests, unavailable values, zero doctors and a stale version save. Record actual results and the database/environment used.

## Decisions needed now, and what can wait

**Now:** designate the one scaffold owner; backend owner confirms/revises the four routes and sample shapes; agree the simulation clock, wait/model meanings, demo travel and shared scenario storage. Decide access controls before enabling a publicly writable capacity route. UI fixture work can proceed while these are resolved.

**Later:** final name, voice/photo integration, real routing, automatic refresh/realtime, advanced forecasts, hospital performance features, native packaging. Do not delay P1 for them.

## Next actions, in order

1. **User:** share the exported patient design with Claude and send the short backend message in [BACKEND-ALIGNMENT.md](BACKEND-ALIGNMENT.md) to your teammate. Confirm who scaffolds.
2. **Backend teammate:** inspect the proposal; return acceptance or exact changes; share any new code on a branch. Start the core comparison/data routes before optional classification.
3. **User + Claude:** inspect repo/design, complete the implementation spec, scaffold once if needed, implement P1/P2 with fixtures and document actual setup.
4. **Third teammate:** compare source checksum with the manifest, maintain matching samples and help test the first connected comparison.
5. **All three:** share the foundation, connect Compare, then capacity change, test in two browsers, and merge small reviewed PRs. Keep progress and evidence on the relevant task/PR.
