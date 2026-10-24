# Project agreement

Use [the build handoff](build/START-HERE.md) for the implementation scope and latest inspected evidence. Keep this summary short.

- Product in one sentence: Our unnamed app compares simulated hospital options and shows the effect of a capacity change on the same scenario.
- Intended users: a patient comparing demo options on a phone, and a hospital user exploring capacity on a dashboard.
- Demo journey, from first screen/input to useful result: choose a demo complaint and origin → compare hospitals → change general-doctor capacity → compare again. See [INTERFACES.md](INTERFACES.md) for the proposed wire contract and toy demo model; the backend owner has not confirmed them.
- Demo capabilities: confirmed photo/description category, patient hospital comparison, shared capacity scenario, hospital dashboard with evaluated demand forecasting and supported performance metrics. Follow [the build checklist](build/BUILD-PLAN.md) for sequencing.
- First checkpoint is a connected comparison with manual category fallback. Native development, clinical triage and live feeds remain out of scope. Real routing and Monte Carlo refinements are optional; speech-to-text comes last. Photo/Gemini intake and forecasting are required follow-on demo tasks, not indefinitely deferred.
- Repository: https://github.com/ajjarm/oxhack-project — owned by ajjarm, public.
- Team GitHub accounts: ajjarm, smsfm598, Zack-Aftab.
- Stack and runtime versions: Next.js App Router with React, TypeScript and Tailwind; backend Route Handlers in the same app; Node.js 24 LTS. Exact dependency versions must be pinned with the first scaffold.
- Package manager: npm, with a committed package-lock.json once the app is scaffolded.
- Deployment target: Vercel for the Next.js app; Supabase Postgres for shared scenario state. No service configuration is verified in this repo or the backend handoff.
- Data source and external services; mock/live status: QueueCare Mock Dataset.json — 5 hospitals, 42,000 synthetic visits, 840 staffing snapshots. Operational values are invented. The original input remains external; fixtures/queuecare/manifest.json records its checksum and the separately added demo journey/model assumptions. No live provider integration exists.
- Integration coordinator for the current period: UNASSIGNED; this person also builds features.
- Shared database/migration and dependency-change coordinator: UNASSIGNED.
- Development data isolation and port allocation: UNDECIDED.

## Decisions

Add only decisions that affect future work: date, choice, reason and affected interfaces. Use GitHub issues for live task status and PRs for change evidence.

## First task: scaffold

One owner creates the smallest runnable application, documents actual setup, pins the runtime and package manager as appropriate, adds safe environment examples, establishes useful checks and CI, and verifies a minimal demo. Other teammates can research, draft fixtures and design interfaces in parallel. Merge this foundation before the first independent implementation branches are created.
