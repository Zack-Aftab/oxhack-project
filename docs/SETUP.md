# Run the app

Stack: Next.js App Router (React, TypeScript, Tailwind) with API Route Handlers in the same app; npm and Node.js 24 LTS; Supabase Postgres for shared scenario state; Vercel deployment. The app was scaffolded on 25 October 2026 on branch `ajjar/app-foundation`; Supabase and Route Handlers are the backend owner's follow-on work in this same app.

The [API proposal](INTERFACES.md) and [frontend samples](../fixtures/queuecare/README.md) drive the UI in sample mode now; the backend owner still needs to confirm or revise the proposal. See [the build handoff](build/START-HERE.md) and the [implementation spec](build/IMPLEMENTATION-SPEC.md).

## Requirements

- Node.js 24 LTS (`.nvmrc` says `24`; `engines` requires `>=24`). The scaffold was verified locally on Node 26.3.1 / npm 11.16.0 and in CI on Node 24.
- npm 10 or newer. `package-lock.json` is committed; use `npm ci` for reproducible installs.
- Python 3 is only needed to regenerate or check fixtures (`scripts/prepare_queuecare_fixtures.py`); it is not part of the app.

Pinned application dependencies: `next 16.4.3`, `react 19.3.0`, `react-dom 19.3.0`, `eslint-config-next 16.4.3`; Tailwind 4 and TypeScript 5 are pinned by the lockfile. After the foundation merges, the backend owner owns dependency, lockfile and env-example changes until the first live comparison works; the frontend lists exact additions it needs in its PR instead of editing those concurrently.

## Install dependencies

```sh
npm ci
```

## Local environment variables

```sh
cp .env.example .env.local
```

`.env.local` is ignored by Git. Variables:

| Name | Who sets it | Meaning |
| --- | --- | --- |
| `NEXT_PUBLIC_DATA_MODE` | everyone | `sample` (default) serves the committed fixtures with an in-memory scenario per browser tab; `live` calls same-origin `/api/...` routes. A failed live request shows an error; it is never replaced with a sample. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL` | backend owner, later | Server-only. Each teammate uses their own development project/keys. Never prefix a secret with `NEXT_PUBLIC_`. |

## Start the application

```sh
npm run dev
```

Opens on <http://localhost:3000>: `/` index, `/patient` phone-first patient screens, `/hospital` operations dashboard. For a second workspace on the same machine:

```sh
npm run dev -- --port 3001
```

A teammate's `localhost` is their laptop. For a phone demo use a reachable deployment or a deliberately configured local-network URL. Sample mode cannot show another browser's changes; only live mode against the same database can.

## Check the application

| Command | What it checks | Needs |
| --- | --- | --- |
| `npm run lint` | ESLint with `eslint-config-next` (core-web-vitals + TypeScript rules) | nothing external |
| `npm run typecheck` | `tsc --noEmit` over `src/` and `contracts/` | nothing external |
| `npm run build` | Production Next.js build (Turbopack) | Google Fonts for Inter at build time |
| `npm run check` | All three in order | as above |
| `python3 scripts/prepare_queuecare_fixtures.py "/path/to/QueueCare Mock Dataset.json" --check` | Committed fixtures match the external source | the original dataset, outside the repo |

There is no unit-test runner yet; add one with the first server-side model or route code. Browser walk-throughs are recorded in each PR.

## Automated GitHub checks

`.github/workflows/ci.yml` runs on pull requests and pushes to `main`: `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build` on Node 24 with `NEXT_PUBLIC_DATA_MODE=sample`. The check appears as **checks / lint, typecheck, build**. Make it required in branch protection only after it has run green on a PR.

## Demo deployment

Target: Vercel for the Next.js app with Supabase Postgres. Import the GitHub repository into a Vercel project; the defaults (framework Next.js, `npm ci`, `npm run build`) work. Set `NEXT_PUBLIC_DATA_MODE` per environment (`sample` until the routes exist, then `live`). Server secrets go in Vercel project settings, never in the repo. Deployment ownership and which scenario each environment uses are still to be decided by the team.
