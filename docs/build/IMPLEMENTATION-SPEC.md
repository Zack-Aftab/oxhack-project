# Implementation spec — patient and hospital frontends

**Status: written 25 October 2026 from the actual designs and checkout; implementation in progress.** Owner: Claude, for Ajjar (frontend). This is the screen-level plan; behaviour rules live in [SCOPE.md](SCOPE.md), the wire contract in [INTERFACES.md](../INTERFACES.md) and [contracts/queuecare.ts](../../contracts/queuecare.ts). No JSON schema is duplicated here.

## 1. Inspected inputs

| Input | Evidence |
| --- | --- |
| Checkout | `oxhack-claude-ready`, branch `ajjar/app-foundation` at `5b77044`, clean; contains PR #1's branch (`ajjar/queuecare-contract`, still open and unmerged against `main` at `4cc3a09`). No app scaffold exists on any remote branch; no newer backend branch was pushed. |
| Patient design | `hackathon design checklist.zip` → `design_handoff_triage/`: `PhoneC.dc.html` (SHA-256 `e29cc785…6085`, five screens at 390×844), `care-logic.js` (prototype state machine with fictional Oxford hospitals), `README.md` (screen-by-screen handoff), `DESIGN.md` (identical to [inputs/hospital-DESIGN.md](inputs/hospital-DESIGN.md) apart from trailing whitespace), `ios-frame.jsx` and `support.js` (device bezel and design-tool runtime; ignored). Unsplash photos are stand-ins and are not used. |
| Hospital design | [inputs/hospital-dashboard.html](inputs/hospital-dashboard.html) (SHA-256 `13ada32d…8931`): sidebar + topbar frame, five tabs, dot-matrix/pill/trend charts, all data from `seed()`, `forecast()`, `pastHours` and localStorage. |
| Data | [fixtures/queuecare](../../fixtures/queuecare/README.md): catalog, baseline/changed/no-travel/unknown/zero-doctor comparisons, baseline/changed dashboards, capacity request, validation error. Demo clock `2026-09-25T18:00:00+01:00`, scenario `demo-1`. |
| Backend | [BACKEND-ALIGNMENT.md](BACKEND-ALIGNMENT.md): no route, database or classifier verified; contract reply pending. Classification, events and forecasting are extension proposals only. |

“Triage” and the plus-mark are placeholders from the design; the app stays unnamed in copy (“this demo”).

## 2. Screen mapping

The design's fictional data (Oxford hospitals, pain score, X-ray, severity, live toast) is replaced by returned contract fields. Anything the contract cannot supply is either omitted or shown as explicitly unavailable; nothing is invented client-side.

### Patient (route `/patient`, phone-first, one client component with `screen` state)

| Design screen | Built as | Data mapping |
| --- | --- | --- |
| **1 Describe** | Two-tone headline, description textarea (“Aa” reveals it; it is the primary input), photo button → `<input type=file accept=image/*>` with preview and **Remove**, origin pill showing the catalog `demoOrigin.label`, safety line (999 / 111 `tel:` links), primary CTA **Continue**. Mic is rendered disabled with the reason “Speech-to-text comes later” (BUILD-PLAN T16). | `GET catalog` for origin and categories. Description/photo are held in component state only; the photo never leaves the browser until a classify route exists. |
| **2 Confirm (intake note)** | Back, “Intake note / Check it before we continue”. YOUR WORDS quote = the user's text (or “No description”). Photo thumbnail with Remove. Intake record rows: **WHAT YOU TOLD US**, **PHOTO**, **CATEGORY** (suggested category when the classifier returns one, otherwise “No suggestion available · choose below”), **WHAT HAPPENS NEXT** (“An estimate from synthetic data, not a diagnosis”). Category chips list all eight catalog IDs by label; the selected ID is what is sent. Demo control (dashed box) toggles the design's 999 screen as a static safety surface. CTA **Find where to go**. | `classify` through the API client. Sample mode returns `suggestedCategory: null` (no classifier fixture exists); live mode calls the proposed `POST /api/classify` once it exists. Exact catalog IDs only; `unknown` is selectable. No pain score, body location, severity scale or X-ray window: the source has no urgency or imaging data. |
| **2′ Red flag** | Copied from the design (wash, status line, Call 999, NHS 111, “Didn't say that?”). Shown only from the demo control, labelled “Demo screen · not triggered by any analysis”. The address line shows the demo origin label. | None. |
| **3 Results** | Back + “Leaving {origin} · {simulationAt HH:MM}”, headline “Where you'll be / seen soonest.”, journey pills **Demo travel** / **Travel unknown** (map to `travelMode` `demo` / `unavailable`; Car/Bus/Walk are not offered because v1 has one invented journey per hospital), mini-map SVG placing the five hospitals by catalog coordinates with an “Illustrative” tag (no origin marker: the demo origin has no coordinates), recommended card for the first ranked row, secondary cards for other ranked rows, dashed unavailable rows for `demo_unavailable` and `unknown`. Footer: notice, `estimateMethod`, scenario/version, **Compare again**. | `POST compare` with `{scenarioId, simulationAt, complaintCategory, originId, travelMode}` from the catalog default plus the confirmed category. Card: name; service line = `explanation`; hero = `totalToReferralMinutes` as dot-matrix numerals labelled “min · demo travel + wait to referral”; journey bar = `travelMinutes` (ink) + `predictedWaitToReferralOnArrivalMinutes` (blue), one scale across cards; white inset “Typical wait · historical mean {meanWaitToReferralMinutes}” → “When you arrive · {estimatedArrivalAt}: {predicted} min” with delta. Unknown values render “—”, never 0. Order is the server's order; the UI never re-sorts. |
| **4 Selected** | Tonal hero (no photo) with name and “Simulated resource match” pill; journey tile Leave {simulationAt} · Arrive {estimatedArrivalAt} · Referral ~{arrival + predicted}; **Historical baseline** card (wait to referral, referral to diagnosis, arrival to diagnosis, sample count) replacing the prototype's expected-queue chart; **Why here** rows built only from returned fields (rank, travel, wait, explanation, snapshot ID); dock **I'm going here** → confirmation “{name} is expecting you · not an appointment”, Change hospital / Cancel. The busyness chart and the “wait dropped” toast are omitted until the forecast/event routes exist. | Row from the last compare response. Intention: sample mode stores it in the in-memory sample scenario (visible on the hospital Scenario queue tab in the same browser); live mode will call the proposed events route. A banner states which of the two happened. |

Mobile layout is the design (390 wide, 20px gutters); on desktop the patient column is centred at 430px max.

### Hospital (route `/hospital`, desktop-first, five tabs from the prototype)

Frame, sidebar, topbar, tokens, charts and table styles are ported from the HTML. Facility = selected hospital (`H001`–`H005` selector in the sidebar), clock = `simulationAt`, status = “Synthetic data · scenario {id} v{version}”. `Date.now()` is never used for simulation values.

| Tab | Source fields | Explicitly unavailable |
| --- | --- | --- |
| Overview | Waiting for referral, waiting for diagnosis, ED spaces (`bedsAvailable`), historical arrivals in window (labelled historical), general + specialist counts, window start/end, baseline staffing status; alerts derived only from these (zero general doctors, zero required specialists, overridden window). Per-hospital comparison bars across the five hospitals. | Hourly arrivals/capacity chart until a forecast route returns a series. |
| Staffing coordination | Table of source roles (general doctors + six specialists) for the selected window; editable **general doctors** for the current window only; **Save** → `PATCH capacity` with `expectedStateVersion`; 409 shows “Someone else changed this scenario” with **Refresh**; CSV export of the displayed table. | Six-window rota, paediatrics, named staff, planning target/gap (needs the schedule/engine extension). |
| Demand forecasting | Historical arrivals in the selected window per hospital and the per-category historical wait baselines for the selected hospital. | 24/48 h arrivals, category mix, ranges, backtest error: rendered as a dashed “Not available until the forecast route exists” block with the horizon selector disabled. No sine wave, no accuracy percentage. |
| Scenario queue | Snapshot counts (`waitingForReferral`, `waitingForDiagnosis`); incoming destination intentions from the API client (sample store in sample mode). Search filters the intention list. | Tickets, P1–P5 priorities, status transitions, mock check-in (needs the events route). |
| Performance | Per-category historical means for the selected hospital: wait to referral, referral to diagnosis, arrival to diagnosis, sample counts; comparison across hospitals for the chosen category. | Occupancy/utilisation, throughput, length of stay, prior-period comparison, feedback save (disabled with reason). |

## 3. Files and ownership

Proposed in SCOPE; created by the foundation unless marked.

| Path | Purpose | Owner |
| --- | --- | --- |
| `package.json`, `package-lock.json`, `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`, `.nvmrc`, `.env.example`, `.github/workflows/ci.yml` | Root scaffold, pinned deps, checks | Claude for foundation; Zack for backend-required dependency/env changes afterwards |
| `src/app/layout.tsx`, `src/app/globals.css` | Inter, design tokens from DESIGN.md §2–5, motion keyframes | Frontend |
| `src/app/page.tsx` | Index linking both experiences and showing data mode | Frontend |
| `src/app/patient/page.tsx`, `src/components/patient/*` | Patient screens | Frontend |
| `src/app/hospital/page.tsx`, `src/components/hospital/*` | Hospital tabs | Frontend |
| `src/components/shared/*` | Mark, notice, mode badge, dot-matrix numerals, journey bar, error/retry, icons | Frontend |
| `src/lib/api/client.ts`, `src/lib/api/sample.ts`, `src/lib/api/live.ts`, `src/lib/api/errors.ts`, `src/lib/api/mode.ts` | One typed client; sample and live adapters | Frontend (shapes come from `contracts/queuecare.ts`) |
| `src/lib/api/proposed.ts` | Types for the proposed classify/events extensions, marked proposed | Frontend; promoted into `contracts/` only with Zack |
| `src/lib/format.ts` | Minutes, 24h clock in Europe/London, nullable display | Frontend |
| `src/app/api/**`, Supabase, migrations | Backend | Zack |
| `src/lib/server/models/**` | Forecast/queue engine | Data teammate |

The tsconfig maps `@contracts/queuecare` and `@fixtures/*` so `contracts/` and `fixtures/` stay the single source.

## 4. Data connection

- `NEXT_PUBLIC_DATA_MODE=sample|live` selects the adapter at build time; the current mode is shown in the UI. Default is `sample`.
- **Sample adapter**: serves the committed fixtures and keeps one in-memory scenario per browser tab: `stateVersion` 0 with the baseline files; a capacity PATCH that matches the fixture (`H001`, 8 general doctors, expected version 0) moves it to version 1 and serves the changed dashboard/comparison; any other PATCH returns `INVALID_REQUEST` explaining that only the fixture change exists; a stale `expectedStateVersion` returns `STATE_CONFLICT`. Compare serves baseline/changed/no-travel/unknown by request; categories without a fixture return a clear error so the retry UI is exercised. Classify returns no suggestion. Intentions are stored in the same tab.
- **Live adapter**: same-origin `fetch` to the four proposed routes plus the proposed classify/events routes; non-2xx bodies are parsed into `ApiError` with the contract's `code`; network failures become `NETWORK_ERROR`. Failed live requests are never replaced with fixtures.
- Blockers: no backend route exists; classify/events/forecast shapes are proposals; the backend owner's contract reply is pending.

## 5. States and checks

Planned UI states: loading skeletons per screen; validation (no category → CTA disabled with reason; oversize/non-image file rejected with message); `travelMode: unavailable` → journey, arrival and total show “—” and cards remain unranked; unknown complaint → all rows unranked with the server explanation; zero general doctors → dashed unavailable row; request failure → error card with the error code/message and **Retry**; 409 on save → conflict banner with Refresh; reduced motion honoured.

Planned checks (record executed results in the PR, not here): `npm run lint`, `npm run typecheck`, `npm run build`; browser walk-through at 390×844 of Describe → Confirm → Results → Selected → intention; hospital Save 16→8 then Compare again shows H001 97→193 / 121→217 in sample mode; conflict path by saving twice with version 0; no-travel and unknown-category screens. Sample mode cannot prove two-browser synchronisation.

## 6. Decisions and next step

- Travel modes, pain score, body location, severity, X-ray, busyness and live toast are design content the contract does not support; they are omitted or marked unavailable rather than faked. Add them only with agreed data.
- `demo_baseline_scaling_v1` numbers are an integration checkpoint; the shared engine will regenerate fixtures and the UI reads whatever `estimateMethod` is returned.
- Dependencies to request from Zack after foundation: none required for the UI slice (no new packages).
- First increment: foundation PR (shells + client + sample/live modes + checks + SETUP). Second: patient screens on fixtures. Third: hospital tabs on fixtures. Then connect catalog → compare/capacity → classify → events → forecast as routes land (BUILD-PLAN T09–T12).
