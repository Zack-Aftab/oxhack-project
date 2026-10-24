# Run the app

Chosen stack: Next.js App Router with React, TypeScript and Tailwind; API Route Handlers in the same app; npm and Node.js 24 LTS; Supabase Postgres for shared state; Vercel deployment. The application has not been scaffolded, so run/check commands below are still unconfigured.

The [API agreement](INTERFACES.md) and [frontend samples](../fixtures/queuecare/README.md) are ready for implementation. The original dataset stays outside the repository. Fixture regeneration/checking uses Python 3's standard library as an offline data tool; it does not add a Python backend.

## The scaffold owner's checklist

- [ ] Choose and record the runtime and its version.
- [ ] Choose and record the package manager and its version, if applicable.
- [ ] Add the smallest runnable app and the appropriate dependency lockfile.
- [ ] Add a safe `.env.example` if environment variables are needed.
- [ ] Replace every placeholder below with actual instructions.
- [ ] Add useful automated checks and a GitHub Actions workflow.
- [ ] Have another teammate follow these instructions from a clean checkout.
- [ ] Verify the smallest demo, then open a PR for review.

## Requirements

Selected runtime: Node.js 24 LTS, with npm. The scaffold owner must pin and verify actual package versions and fill in the remaining instructions.

## Install dependencies

Not configured yet.

## Local environment variables

Not configured yet. Explain each required variable and how each teammate obtains their own suitable development values. Never put real credentials in this document.

## Start the application

Not configured yet. Include the local URL and instructions for using a different port when two workspaces run at once.

## Check the application

Not configured yet. Record actual test, lint, type-check and build commands as applicable. Distinguish checks we can run locally from checks that need external services.

## Automated GitHub checks

Not configured yet. Once a real workflow has run successfully, record its exact check names. Only then make those checks required if GitHub protection is available.

## Demo deployment

Target: Vercel with Supabase Postgres. Service connections and database migrations are not configured yet. Decide who owns deployment configuration and which scenario each development environment uses.
