# Prompt for Zack's coding agent — database and backend

Use the coding environment that can inspect Zack's actual database work and write/push repository files. A chat without those tools must report its limitation rather than invent a PR or successful connection.

```text
You are helping Zack, database/backend owner for:
https://github.com/ajjarm/oxhack-project

Inspect and preserve the Supabase database/work Zack has already built.
Claude owns the ONE Next.js app foundation and both frontends. Do not create
another frontend or app scaffold. You own database integration, server routes,
calculations and API contracts.

PART A — DO NOW
1. Inspect your actual schema, imports, local files and any existing API code.
   Read AGENTS.md and the context on ajjar/queuecare-contract, PR #1 (or main
   if merged): docs/build/START-HERE.md, BUILD-PLAN.md, MODELS-AND-DATA.md,
   docs/INTERFACES.md and contracts/queuecare.ts.

2. On your own zack/database-handoff branch, publish actual schema/SQL,
   migrations/import instructions and existing backend code, preserving work.
   Do not reset or destructively change the existing shared database.

3. Add docs/build/BACKEND-CONNECTION.md with actual tables/columns/keys,
   verified import counts, existing endpoints with request/response examples,
   setup/test commands and required environment-variable NAMES, not values.
   Mark tested versus planned. If no API exists, explicitly say:
   "Database ready; API not implemented."
   Compare the proposed contract with your actual implementation; record exact
   differences. It is a proposal, not a reason to discard existing work.

4. Push/open a PR. Return DATABASE_HANDOFF_READY and its link. Zack gives
   Ajjar the link. Share Supabase access/configuration privately; never commit
   or paste passwords, privileged keys or real .env files into the handoff.
   If tools/access prevent publishing, report the exact blocker honestly.

PART B — WHEN AJJAR SENDS CLAUDE'S FOUNDATION_READY PR LINK
5. Fetch that exact foundation and create your own zack/backend branch from it
   (or updated main if merged), declaring any unmerged dependency. Bring your
   database work into that SAME app. Do not generate a competing scaffold.

6. First implement GET /api/catalog reading real hospitals/categories from
   Supabase. Agree any necessary shape changes by updating docs/INTERFACES.md,
   contracts and matching fixtures together. Prove an actual database-to-HTTP
   response. Publish your backend PR and return CATALOG_READY, PR link, setup
   instructions and the real response/test. Ajjar passes this link to Claude.

7. Continue compare, dashboard read and persisted capacity updates, followed
   by the Gemini classification, forecast and scenario-event tasks in
   BUILD-PLAN.md. Use one shared ranking/forecast/queue engine for both screens;
   integrate the third teammate's model/data work if supplied. The initial toy
   fixture model is only an integration checkpoint, not the final forecast.
   Publish exact contract changes before the frontend implements those shapes.

After the foundation, you own backend-required package/lock/env-example and
contract edits until the first live comparison works; Claude owns frontend
pages/components/styles/API client. Don't edit his frontend files.
Use ignored server configuration for secrets. Keep scenario/version consistent,
validate inputs, protect demo writes, and distinguish intent from check-in.
Test routes without waiting for finished screens. Report actual results and
publish focused PRs for teammate review.
```
