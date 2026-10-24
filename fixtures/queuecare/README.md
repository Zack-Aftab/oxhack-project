# Small frontend samples

**Start with [compare.response.json](compare.response.json) for the patient cards and [dashboard.response.json](dashboard.response.json) for the hospital screen.** These use real source IDs and synthetic source values. The complete agreement is [docs/INTERFACES.md](../../docs/INTERFACES.md); shared wire types are [contracts/queuecare.ts](../../contracts/queuecare.ts).

These files do not create API endpoints or configure Supabase. The contract is proposed, pending backend-owner agreement. See [the build handoff](../../docs/build/START-HERE.md). The app has no name yet; existing `queuecare` paths and schema IDs are temporary technical names.

| File | Use |
| --- | --- |
| [catalog.response.json](catalog.response.json) | Hospital/category options and default request |
| [compare.request.json](compare.request.json) | Exact request for the baseline patient example |
| [compare.response.json](compare.response.json) | Five patient cards; explicitly invented demo travel plus toy baseline estimate |
| [dashboard.response.json](dashboard.response.json) | Baseline hospital capacity, queues and historical wait summaries |
| [capacity.request.json](capacity.request.json) | PATCH body setting H001's general doctors to 8 at the selected time |
| [dashboard.capacity-changed.response.json](dashboard.capacity-changed.response.json) | PATCH response and subsequent dashboard at version 1 |
| [compare.capacity-changed.response.json](compare.capacity-changed.response.json) | Patient comparison after that same change |
| [compare.no-travel.response.json](compare.no-travel.response.json) | Travel not configured; arrival-time and total estimates are null |
| [compare.unknown-category.response.json](compare.unknown-category.response.json) | Unknown complaint: no asserted match or predicted wait |
| [compare.no-general-doctors.response.json](compare.no-general-doctors.response.json) | H001 has zero general doctors: unavailable, no divide-by-zero result |
| [error.validation.response.json](error.validation.response.json) | Example HTTP 422 response |
| [manifest.json](manifest.json) | Original source checksum, counts, generation assumptions and added demo travel values |

## How your UI uses them

One API client supplies data to the components. In sample mode it loads these files. In connected mode it calls the endpoints and returns the same shapes. Match changed dashboard and comparison fixtures by `scenarioId` and `stateVersion`; do not mix version 0 and 1.

Keep an obvious synthetic-data notice. Label the journey values **Demo travel** and the estimate **Simulated wait to referral**. A historical arrival-to-diagnosis mean is a separate measure, not travel-plus-wait.

Do not fall back to sample data silently when the real API fails. Show an error and retry.

## Source-derived versus added

- Hospital identities, staffing/queue snapshots, categories and historical wait means come from the supplied synthetic input.
- Travel durations are added illustrative fixtures, not output from the input dataset or a maps API.
- Staffing-effect estimates are added using the explicitly documented `demo_baseline_scaling_v1` rule. That rule only illustrates a scenario and does not establish clinical or operational validity.

To rebuild the examples, keep the original dataset outside this repo and run from the repo root:

```sh
python3 scripts/prepare_queuecare_fixtures.py "/path/to/QueueCare Mock Dataset.json"
```

To check the committed files without changing them:

```sh
python3 scripts/prepare_queuecare_fixtures.py "/path/to/QueueCare Mock Dataset.json" --check
```

This uses only Python's standard library. Python is an offline fixture-preparation tool here; it does not change the chosen TypeScript application stack.
