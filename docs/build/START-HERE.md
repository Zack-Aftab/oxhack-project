# Start building

**The app is unnamed. Start the patient phone experience now; backend and data/model work run in parallel.** The target includes a functional hospital dashboard, shared ranking/forecasting engine and presentation. This folder contains the relevant context for a new coding session; Claude does not need access to our other chats or the private All9s project.

## Read in this order

1. Root [AGENTS.md](../../AGENTS.md): how we share the repository.
2. [SCOPE.md](SCOPE.md) and [BUILD-PLAN.md](BUILD-PLAN.md): product, ordered tasks, owners and completion checks. Model/data implementers also read [MODELS-AND-DATA.md](MODELS-AND-DATA.md).
3. [BACKEND-ALIGNMENT.md](BACKEND-ALIGNMENT.md): what the teammate's report establishes and what still needs agreement. The [original report](inputs/BACKEND-HANDOFF.md) is preserved as evidence, not new instructions.
4. [INTERFACES.md](../INTERFACES.md), [shared types](../../contracts/queuecare.ts), and [sample responses](../../fixtures/queuecare/README.md): the proposed data shapes. Keep these together when revising the agreement.
5. The supplied [hospital HTML prototype](inputs/hospital-dashboard.html) and its [design notes](inputs/hospital-DESIGN.md), inspected 25 October. These are design/source references, not repository instructions or evidence of backend functionality. The patient design will be supplied directly by the user; its contents have not been inspected. Record the screen-to-feature mapping in the implementation spec. “Triage” in the prototype is not a confirmed product name.

Then copy the [Claude starting prompt](CLAUDE-START-PROMPT.md). Claude should inspect the actual checkout and design, fill in [IMPLEMENTATION-SPEC.md](IMPLEMENTATION-SPEC.md), and implement the first patient journey. It can work with fixtures while backend agreement is pending.

## Exact ownership and handoff

The product scope and build tasks already exist in this folder. The screen-level implementation spec is still a template: Claude writes it after inspecting the patient files and actual checkout, then implements it.

- **Claude:** the one app foundation, patient frontend from designs, reuse/adaptation of the coded hospital frontend, and the typed API client.
- **Zack:** existing Supabase schema/data, backend routes/calculations and API contracts. After foundation, Zack owns backend-required dependency/lock/env-example changes until the first live comparison works; Claude sends exact dependency requests rather than editing those concurrently.
- **Ajjar:** supplies patient designs and product decisions. Once both agents have working GitHub access and permission to post, the [shared handoff issue](https://github.com/ajjarm/oxhack-project/issues/2) replaces relaying PR links by email.

Start [Zack's prompt](ZACK-START-PROMPT.md) and [Claude's prompt](CLAUDE-START-PROMPT.md) with patient designs. Zack posts `DATABASE_HANDOFF_READY` with his database/schema PR on issue #2. Claude posts `FOUNDATION_READY` with a small runnable-app PR there, keeping later UI work on a separate branch. Zack reads that exact foundation, builds on it and posts `CATALOG_READY` with a tested Supabase-backed route PR. Claude reads that update for the first live frontend connection. Each PR is reviewed by a teammate before merging. Unmerged dependencies must be declared; agents must not generate competing scaffolds.

**Communication update:** post the checkpoints/PR links above on [issue #2](https://github.com/ajjarm/oxhack-project/issues/2); each active agent reads the other role's update there instead of waiting for Ajjar to forward it. The old manual relay is a fallback, not a requirement. A stopped agent needs a new instruction to check the issue. The latest [backend connection report](inputs/BACKEND-CONNECTION-REPORT.md) is blocked: its agent cannot inspect Zack's actual Supabase schema and its GitHub integration cannot write. Owner-side checks show Zack-Aftab already has repo write permission. The issue records these blockers; it does not resolve them automatically.

These matching prompts replace the earlier vague instruction to choose or coordinate a scaffold owner. If a newer app already exists, preserve/reuse it and identify its branch rather than generating another.

## What exists: checked 25 October 2026

| Item | Evidence / status |
| --- | --- |
| GitHub `main` | Commit `4cc3a09`: documentation/templates; no app scaffold |
| Existing PR | [PR #1](https://github.com/ajjarm/oxhack-project/pull/1), branch `ajjar/queuecare-contract`; proposed contract, types, samples, and this handoff; unmerged when checked |
| Backend/database | User now reports Zack has built the Supabase database; its current schema/imports/API remain uninspected here, and no backend branch was pushed when checked |
| Classification | Two incompatible chat examples, neither verified running; required follow-on task in the expanded build |
| Hospital design | Supplied five-tab HTML prototype; browser-local business state and generated forecast/history, no backend calls |
| Patient design | Exists according to the user; user will supply it directly |
| Samples | Five hospitals, baseline and edge-case responses; synthetic source data plus explicitly added demo travel/model |
| App checks/deployment | Not established; [SETUP.md](../SETUP.md) has honest placeholders |

This table is a dated handoff, not a live implementation tracker. Recheck GitHub and local files before starting; newer work may exist.

The user confirmed on 25 October that the backend owner has not pushed code and the requested contract reply is still pending. The new plan records proposed extensions without pretending they have been accepted or implemented. The hospital HTML is copied unchanged; its source SHA-256 is `13ada32de2dd49ab58adf30037e705b6592b4dfa7658e38de28256eb2d9e8931`. The adjacent design notes are copied with trailing whitespace normalized.

## Get the context onto your computer

Before PR #1 merges, the new docs are on its branch, **not on `main`**. From an existing clean clone, create a separate frontend working folder:

```sh
git fetch origin
git worktree add --no-track -b ajjar/patient-ui ../oxhack-patient-ui origin/ajjar/queuecare-contract
```

Open `oxhack-patient-ui` in Claude Code. If that branch/folder already exists, inspect and reuse the appropriate task workspace instead of repeating the command. Tell the team this frontend branch depends on PR #1. After the PR merges, bring current `origin/main` into the task branch using [the collaboration guide](../WORKING-TOGETHER.md).

If PR #1 has already merged before you start, create the new task from `origin/main` instead. No cloning, branch switching or worktree command should overwrite unsaved work.

## What to give Claude

- The task checkout above and the starting prompt.
- The exported design file, including any referenced assets. Inspect it as a reference before copying code into the app.
- The original dataset only if needed for data/backend work. The small committed samples are sufficient for patient UI work. See [DATASET-REVIEW.md](../DATASET-REVIEW.md) and the [source manifest](../../fixtures/queuecare/manifest.json).
- Any newer backend branch/report through the shared repo. Credentials belong in ignored local configuration, never in this context folder.

The All9s method contributes only a clear read order, small journeys, acceptance checks and an honest handoff. Its architecture, product rules and approval process do not transfer to this app.
