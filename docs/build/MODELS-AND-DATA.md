# Models, data and integration plan

**Implementation proposal · 25 October 2026 · backend-owner reply pending.** This is the technical design for T03/T06/T07/T12 in [BUILD-PLAN.md](BUILD-PLAN.md), not implemented algorithms or an accepted replacement API. Keep the existing fixture UI working; reconcile extensions with the backend owner before changing shared types.

## What the data supports

The original synthetic file has five hospitals, 42,000 visits with arrival/referral/diagnosis timestamps, and 840 four-hour staffing/queue snapshots. The [dataset review](../DATASET-REVIEW.md) and [manifest](../../fixtures/queuecare/manifest.json) own source meanings/checksum.

| Available | Missing — do not invent as a source fact |
| --- | --- |
| Hospital coordinates; eight complaint categories; six specialist counts plus general doctors | Routing durations, clinical severity/P1–P5, patient age/paediatrics, real care capability certification |
| Referral waits, diagnosis intervals, historical arrival timestamps | Doctor-seen/discharge timestamps, actual treatment completion, length of stay |
| Snapshot queues and available ED treatment spaces | Total/occupied/cleaning/reserved beds, measured per-doctor service rate, named staff/rota |

All operational records are invented. Exactly 300 visits per hospital per day limits what a model can learn about daily totals. Demonstrate within-day demand/category patterns and scenario sensitivity; do not claim real-world forecast accuracy or causal staffing effects.

For historical wait summaries, include an interval only once its end event is at or before the scenario clock: referral for the first wait, diagnosis for the second/total. State whether a chart groups records by arrival or completion window. Never expose later outcomes just because the full JSON already contains them.

## One engine, two screens

Implement pure server-side functions for `forecastArrivals`, `projectQueue`, and `compareHospitals` (suggested names, not existing code). Both dashboard and comparison handlers call them with the same `scenarioId`, `stateVersion`, `simulationAt`, model version and capacity schedule. Cache by those inputs; a capacity save changes the version and invalidates/rekeys derived results.

The current `demo_baseline_scaling_v1` fixtures are an initial integration checkpoint. They average the full source history and **must not be used as past-only forecast evaluation**. The forecast/queue model needs a new model identifier and regenerated matching examples; its numerical results will differ. Preserve the source hospital/category IDs.

## 1. Forecast arrivals and category mix

**Target:** hourly arrivals by hospital for 24 h, then 48 h; category counts/proportions; an uncertainty range; reproducible evaluation.

1. Aggregate visit `arrival_at` into complete hourly bins in Europe/London. Fill genuinely observed empty bins with zero; distinguish missing coverage. At a forecast origin, use only records/events available before `simulationAt`. Do not use the source snapshot's `arrivals_during_next_4h`: it contains the future outcome.
2. Keep a seasonal-naive baseline: the count in the same hour seven days earlier. Test a shrinkage model combining mean same-weekday/hour counts with mean same-hour counts from recent days. Use `w = n / (n + k)`, where `n` is the number of matching historical weekday/hour observations. Tune only a small predefined set, e.g. `k = 0, 2, 4`, on the validation period; document the chosen recent-day window. If it does not improve the validation result, keep the simpler baseline.
3. Estimate category proportions from past counts, smoothing sparse hospital/time groups toward that hospital's overall category mix. Multiply the hourly total by those proportions. Keep expected counts as decimals internally; reconcile displayed integer category counts to the displayed total rather than rounding each independently.
4. Use validation forecast residuals for an empirical range. Pool sparse groups explicitly and report sample counts; check actual held-out coverage before calling it a calibrated interval. No hard-coded ±4 or self-reported model confidence.

**Chronological evaluation:** initial fit 21 September–4 October; tune on rolling forecast origins 5–11 October; freeze method/parameters and evaluate on 12–18 October. At each origin, inputs precede that origin; later observations are only scoring targets. State whether the final test uses a frozen fit or rolling refits with already observed data; never retune on that test. Only score horizons fully covered by the dataset.

Report **MAE in arrivals/hour**, number of evaluated bins, date range, per-hospital/horizon results, baseline MAE and observed interval coverage. If adding WAPE, return unavailable when summed actuals are zero. Replace “98% accurate” with the actual metric, e.g. “MAE: X arrivals/hour on held-out synthetic history”; X must come from executed evaluation.

Recommended forecast demo clock: **2026-10-12T08:00:00+01:00**, on a staffing boundary after three weeks of history. This is a proposed change from the existing September fixture clock. Update scenario defaults, requests and all related samples together after agreement; do not silently mix clocks. The real computer date is not the simulation date.

These evaluation choices follow [past-only rolling-origin evaluation and forecast-error measures](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation). The particular model and split above are our proposed hackathon design, not claims from that source.

## 2. Project queue and staffing effects

Use a transparent queue-conservation model in five-minute steps:

```text
arrivalsInStep = forecastArrivalsPerHour * (5 / 60)
capacityInStep = effectiveReferralsPerHour * (5 / 60)
served = min(queue + arrivalsInStep, capacityInStep)
nextQueue = max(0, queue + arrivalsInStep - served)
```

Start from the selected snapshot's queue at the scenario clock, then apply explicit scenario events. The first demo clock is a snapshot boundary, avoiding an invented within-window observation. The source snapshots and visit timelines need not form a consistent event simulation: do not silently combine two independently reconstructed queue totals.

There is no measured service capacity. A defensible **simulation parameter**, not a clinical productivity estimate, is historical referral events per general-doctor-hour in complete past windows. Count only referrals already recorded by the cutoff and sum the corresponding nonzero staffing-window doctor-hours. Document fallback/missing-data handling; reject nonpositive/unknown rates for ranking rather than divide by zero. Under the illustrative assumption of linear scaling:

```text
effectiveReferralsPerHour = generalDoctorsAvailable * calibratedSimulationRate
```

This is a throughput proxy used to parameterize a toy scenario, not proof that doubling doctors halves actual waiting time. Specialist availability gates a category match; the current data does not justify a separate specialist-speed coefficient. Available bed count can be shown; do not invent bed utilisation or a bed-delay coefficient.

For future staffing, carry the last known baseline count forward as an explicit assumption unless an explicit scenario schedule replaces it. Do not treat future source snapshots as observed staffing at the forecast origin. A v1 capacity override affects its documented four-hour window only; carry the baseline outside it. Six-block rota editing requires an agreed schedule extension with window-specific overrides.

To estimate wait at an arrival time, project the backlog until that time, then estimate how long the **queue ahead** takes to clear using subsequent capacity. With constant capacity, the approximation is `60 * queueAhead / referralsPerHour`; with changing capacity, integrate forward until cumulative capacity clears it. This is a modelled wait-to-referral proxy, not completed treatment. If capacity is zero throughout the supported horizon or clearance exceeds it, return unavailable/out-of-horizon explicitly. Never replace that with a finite best-case number.

Patient waiting and hospital queue/wait charts must use this same calculation. Staffing recommendations can show the smallest integer general-doctor count whose projected backlog meets an explicit **demo planning target**, searching within a bounded range. Return “target not met” if none does. Targets/rates are scenario assumptions, not approved clinical staffing requirements.

**Optional enhancement after the deterministic engine works:** run a fixed-seed ensemble using blocks of validation arrival residuals, preserving time correlation, then report median/range and ranking stability. Use common draws before/after a staffing edit. Report empirical coverage and avoid a clinical certainty claim. This enhancement must not delay the working shared model.

## 3. Rank hospital options at arrival time

1. **Confirm the category.** Gemini suggests one catalog ID; the user confirms or changes it. Unknown stays unknown. Do not let Gemini generate hospital waits, capacity or urgency.
2. **Resolve travel.** Start with the committed, explicitly labelled demo-origin travel minutes. Coordinates can additionally support straight-line distance, labelled as such. For arbitrary origins, add a routing provider behind a server adapter; coordinates/distance alone are not road travel time. Unknown travel makes a travel-inclusive total unavailable.
3. **Apply resource constraints.** Check known general-doctor availability and category-specific specialist availability at arrival under the scenario. Zero required capacity is unavailable; missing evidence is unknown. This is only a simulated resource match. A separate predefined demo care-pathway constraint may restrict destinations, but source records do not establish real clinical suitability/opening restrictions.
4. **Project on arrival.** For each remaining hospital, set `arrival = simulationAt + travelMinutes`, run the common queue engine to that point, and obtain the wait proxy. Evaluate within supported clock/horizon bounds.
5. **Rank by `travelMinutes + predictedWaitToReferralOnArrivalMinutes`, ascending**, with hospital ID as a stable tie-break. Show each component and a backend-produced explanation. Do not add distance as another penalty when travel already represents the journey. Show uncertainty/coverage separately; unsupported rows stay visible but unranked.

Severity should be a **care-pathway constraint**, where independently established, not an arbitrary `severity * wait` weight. The source has no urgency labels; image/description classification does not supply them. In this prototype, keep urgency unknown or use separately authored, clearly synthetic cases; never infer P1–P5 from a photo or pain score. Do not call the fastest modelled option the clinically best hospital.

Test: hospital with shortest travel can lose to a lower arrival-time queue; unavailable specialty cannot win through short travel; more doctors cannot worsen the same hospital's predicted wait with all other inputs fixed; increasing starting queue cannot reduce its wait; deterministic ties; zero/missing capacity; missing routing; late arrival crossing a staffing-window boundary.

The technical depth is the shared time-dependent model, constraints, reproducible validation and explanations—not a complicated unexplained weighted score.

## Data and fixtures to prepare

**T03 deliverables:** small JSON responses matching the final agreed types, a documented source/import checksum check, and a repeatable named-scenario seed/reset. Existing [fixtures](../../fixtures/queuecare/README.md) already cover the first simple comparison, dashboard and capacity cases. Do not ask the frontend to invent a second hospital dataset.

- Classification: text-only, image+text and unknown suggestions; exact category ID and confirmation flag; provider failure. Use permitted synthetic/example images and authored descriptions; no real patient images are required for the demo.
- Forecast: 24/48 h hourly points, category mix, range, training cutoff, model/version, actual historical comparison points and genuine evaluation summary. Include no-history and sparse-category examples. No new forecast examples have been generated by this planning change.
- Capacity/ranking: baseline versus changed state from the new engine, with same scenario, clock, hospitals and random seed where relevant. Mark which figures are source-derived, estimated or scenario assumptions.
- Patient-to-hospital: destination intention, explicit arrival, referral and diagnosis events with IDs/timestamps; duplicate submission and stale-version examples. Queue/ticket samples must reconcile with the scenario's queue aggregate. If seed tickets materialize the snapshot backlog, do not add that backlog again.
- Rehearsal: one case, origin and hospital staffing change chosen after running the engine to demonstrate an observable effect. Reset restores only that scenario's synthetic state. Don't hard-code a winning hospital or fake a rank change.

The full dataset can remain outside Git and be imported server-side. Record actual import commands/location and scenario metadata so every teammate can reproduce the same demo. No source generator or import was changed by this document.

## Backend changes to agree

Keep the four [existing proposed routes](../INTERFACES.md) as the initial comparison milestone. Before implementing expanded interfaces, backend + UI owners update that owning document, TypeScript types and matching fixtures together. The following names are **extension proposals**, not existing handlers or a second accepted contract:

| Extension | Minimum agreement |
| --- | --- |
| `POST /api/classify` | Multipart `image` optional + `symptoms` optional; at least one. Success: `suggestedCategory` uses the catalog enum; `requiresConfirmation: true`. Pick consistent error envelope/status/limits rather than retaining both chat variants. Validate file bytes/type/size and structured provider output server-side; use manual fallback on failure. |
| `GET /api/scenarios/{scenarioId}/forecast` | `hospitalId`, `simulationAt`, `horizonHours`; return hourly expected arrivals/category counts/range, projected queue/wait/capacity, model version/training cutoff/evaluation metadata and the scenario version actually used. Forecast-specific fields must not be silently inserted into the old literal model type. |
| Extend existing dashboard read | Requested hospital/history window, supported historical metrics, incoming intentions and anonymous scenario queue; identify source-snapshot versus model/event-derived measures. Add feedback persistence only if its UI is kept active. |
| `POST /api/scenarios/{scenarioId}/events` | Proposed event kinds: destination selected, arrival confirmed, referral recorded, diagnosis recorded. Agree IDs, permitted transitions, timestamps and category/hospital links; require idempotency and atomic version checks for mutations. Patient intent alone never creates an arrived patient. Staff events require the agreed demo access control. |
| Optional staffing schedule extension | Target window start/end and general-doctor count, expected scenario version; keep the clock separate from the edited future window. Read-only specialist rows until their effect is modelled. |
| Protected scenario reset | Restore one named synthetic scenario for rehearsal without wiping source history or another person's scenario. Decide route/action with API owner; do not expose unrestricted public reset/writes. |

Use server-side Gemini credentials and schema-constrained category output. Google's [structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output) supports predefined category schemas; [image-understanding documentation](https://ai.google.dev/gemini-api/docs/image-understanding) covers combined image/text input. Schema validity is not proof that the category is correct: validate, allow unknown and require user confirmation. Pin an available model during implementation; this plan does not assume a model name or provider call already works.

## Evidence for the presentation

Show one real backend response, one held-out forecast evaluation against a baseline, and a repeatable before/after staffing comparison from the shared engine. Distinguish the live Gemini call, historical synthetic records, forecast and what-if assumptions. Do not present observed synthetic prediction error as accuracy on real hospitals, or modelled time differences as actual patient time saved.
