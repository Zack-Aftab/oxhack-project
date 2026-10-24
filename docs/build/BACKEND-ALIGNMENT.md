# What the backend handoff means

The [report supplied by the teammate](inputs/BACKEND-HANDOFF.md), dated 24 October 2026, verifies **no running core API, database import or shared scenario**. It describes empty local classifier files and two unexecuted classifier snippets. That does not prove the teammate has no newer work elsewhere; ask for its branch if they do.

We checked GitHub at this handoff: only `main` and `ajjar/queuecare-contract` were present, with no application scaffold. The report's GitHub-access failure is a limitation of its session, not evidence that the repository or PR does not exist.

## Reconciliation

| Topic | Finding and next action |
| --- | --- |
| Stack | Report repeats the same planned Next.js/Supabase stack. Express is an alternative classifier experiment, not a confirmed replacement architecture. |
| Core API | Report defines no comparison/dashboard/capacity contracts and could not read PR #1. Our four-route proposal therefore remains proposed, rather than contradicted or accepted. |
| Dataset | Same hospital IDs, category mapping, minute definitions and synthetic-data limitations. Its differently named file has no recorded checksum: confirm bytes before treating it as the identical input. |
| Wait calculation and travel | Report has neither implemented. Our scaling formula and invented demo travel are reference options, not the teammate's algorithm. Confirm or replace them explicitly. |
| Shared state | No verified store or synchronization. Supabase is the selected target; schema, import, overrides and version handling still need implementing. |
| Classification | `/classify` returns human labels; `/api/classify` returns a category ID plus confirmation flag. These are untested alternatives, not two agreed APIs. |
| Category mismatch | A snippet uses `other_uncategorised`; dataset/fixtures use `other_or_uncategorised`. Normalize and validate suggestions against the catalog before use. Do not change the dataset enum to match a typo. |
| Design | Not supplied to this review. Visual controls do not establish backend capabilities. |

No core JSON payload needs changing merely because of this report. There is also no evidence that the backend owner has accepted the existing shapes. Keep using the proposal for sample UI, and settle differences in [INTERFACES.md](../INTERFACES.md), [types](../../contracts/queuecare.ts) and affected [fixtures](../../fixtures/queuecare/README.md) together.

## Send this to the backend teammate

Copy this message yourself; no message has been sent on your behalf:

> The handoff doesn't verify a working core API/database yet, so we're starting the patient UI with samples. Please give your AI access to https://github.com/ajjarm/oxhack-project/pull/1 — branch `ajjar/queuecare-contract` — and ask it to read `docs/build/START-HERE.md`, `docs/INTERFACES.md`, `contracts/queuecare.ts` and the fixtures. The app has no name yet.
>
> Confirm whether you accept the four proposed routes and JSON shapes. If not, return exact changes with request/response examples. Also confirm or change the demo clock, travel values and proposed wait formula; explain shared scenario storage and access for capacity updates. Mark what works versus what is planned, and give us your actual code branch and run commands when available. Don't rewrite existing work just to match a proposal.
>
> We're recommending one Next.js app, not separate frontend and Express apps. Please confirm who creates the initial scaffold so we don't both generate one. Let's connect Compare first, then shared capacity changes. Image classification can follow; any suggestion must use the catalog category IDs and allow user confirmation. If you can't access the PR, say so and we'll send the contract files directly.

The developer must know the contract even if someone else wrote it. This short acknowledgement prevents parallel implementations from quietly diverging.

## Expanded work requested 25 October

The user confirms no backend branch has been pushed and the above reply is still pending. They now require photo/description categorization, technical ranking depth, evaluated hospital forecasting, a functional demo and presentation. Send the backend owner [BUILD-PLAN.md](BUILD-PLAN.md) and [the extension proposals](MODELS-AND-DATA.md#backend-changes-to-agree) alongside the original message. Classification is now required follow-on demo work; Compare remains the first connection to get working. Do not wait for all later endpoints to begin fixture UI/data work.
