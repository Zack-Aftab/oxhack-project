# Run the app

The selected stack is Next.js App Router, TypeScript, Tailwind CSS, Next.js Route Handlers, Supabase Postgres, and Vercel, using Node.js 24 LTS and npm. The application scaffold is still pending.

Database schema, import commands, credential setup, and verification are documented in [DATABASE.md](DATABASE.md). Database tooling uses Node.js built-ins and needs no npm install.

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

Not chosen yet.

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

Not chosen yet. Decide who owns deployment configuration and which services or database each environment uses.

## Selected simulation and database workflow

Use [simulation/README.md](../simulation/README.md). Python standard library runs the simulator; Node.js 24 built-ins back up and import Supabase data. These tools do not require an application scaffold or running web server. The chosen 30-day compressed dataset and its summaries are committed under `simulation/results/month-v5/`.

## Standalone Gemini intake demo

The edited Express server and page are runnable with Node.js 24 and npm. See [DEMO-SETUP.md](../DEMO-SETUP.md) for credentials, model configuration, required files and checks. This does not scaffold the agreed Next.js app or save intake data to Supabase.
