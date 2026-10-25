# Prompt for Claude Code — foundation and both frontends

Supply the patient design exports/screenshots with this prompt. Zack gets [his matching prompt](ZACK-START-PROMPT.md). The [shared handoff issue](https://github.com/ajjarm/oxhack-project/issues/2) replaces copying responses between chats when both agents have access.

```text
Build our unnamed hackathon app's frontend in:
https://github.com/ajjarm/oxhack-project

YOU own the single Next.js app foundation and both frontends. Zack owns
Supabase, backend routes/calculations and API contracts. Ownership is fixed.

Use https://github.com/ajjarm/oxhack-project/issues/2 for handoff updates.
You may read/comment there for this project: prefix FRONTEND, post checkpoints
and PR links, and check latest comments at meaningful milestones. Read Zack's
backend PR from that thread instead of waiting for me to relay it. This does
not wake idle agents. Report read/write errors honestly; keep independent UI
work moving. No secrets in comments.

Hospital screens already exist as coded HTML:
docs/build/inputs/hospital-dashboard.html
Reuse their layout/styles and adapt them into the app; don't redesign them.
Patient screens have only the designs/screenshots I supply: implement those.
Zack reports Supabase is ready, but its schema/API details are pending.

1. Inspect the actual checkout, unsaved work and newer remote code. Preserve
   existing work. Clone into a fresh folder if needed. The context is on branch
   ajjar/queuecare-contract (PR #1); start your own task branch from it if still
   unmerged, or current main if merged. Never implement on main/context branch.

2. Read AGENTS.md, docs/build/START-HERE.md, SCOPE.md, BUILD-PLAN.md,
   MODELS-AND-DATA.md, docs/INTERFACES.md, contracts/queuecare.ts and fixtures.
   Complete docs/build/IMPLEMENTATION-SPEC.md from the real designs/repository:
   screens/interactions, files, data mapping, UI states and acceptance checks.
   Link the API proposal rather than inventing another schema. Then build;
   don't stop for approval of routine implementation details.

3. FIRST publish a small foundation PR: reuse any newer app; otherwise create
   one Next.js App Router/React/TypeScript/Tailwind app with npm/Node 24 LTS,
   patient/hospital page shells, typed API client, explicit sample/live modes,
   and actual setup/check commands. Supabase and Route Handlers belong to this
   same app; Vercel is the deployment target. Return FOUNDATION_READY, PR URL,
   branch/commit and run/check commands. Post that checkpoint on issue #2 for
   Zack to read; don't wait for me to forward it.

4. Continue frontend work on a SEPARATE task branch based on the foundation;
   keep later UI commits out of the foundation PR Zack uses. Build the patient
   design first: description, photo preview/remove, confirmed category, hospital
   comparison and destination selection. Use the committed fixtures while API
   work is pending. If design files are inaccessible, ask for their location
   and continue foundation/client work; don't invent unseen screens.

5. Bring the existing hospital screens into the app and bind them through the
   API client. Follow BUILD-PLAN.md's five-tab mapping for missing source fields.
   No separate frontend ranking/forecast formula or fake functioning controls.

6. When Zack posts CATALOG_READY/backend PR on issue #2 (or I supply it), read
   docs/build/BACKEND-CONNECTION.md and the
   actual routes/types. Bring the reviewed backend into your branch preserving
   work. Connect catalog first, then compare/capacity, then classification,
   events and forecasting as available. Never silently replace failed live
   requests with samples; never put privileged database keys in browser code.

After foundation, Zack owns package/lock/env-example and API-contract changes
until the first live comparison works. Use existing dependencies; list any
exact additions you need in your handoff for him. You own frontend files.
Do not invent database columns, a product name, clinical severity or forecasts.
Keep synthetic-data and correct wait labels. Speech-to-text is last.

Run real checks and visual/browser checks where available. Push focused PRs
for teammate review. Report sample/live status, evidence and remaining work.
```
