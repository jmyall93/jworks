# JWorks 10.2 Cloud

Cloud migration branch of JWorks, based on JWorks 10.1.4 Fresh Start.

## Included from 10.1.4
- JWorks Command Center + Focus Deck
- Pending Dependency terminology
- Project-only Gantt
- Editable AI-generated task plans (edit/add/remove/reorder before creation)
- Fresh-start data model; no user/project/task data or API keys are committed

## Cloud architecture
- Cloudflare Python Worker + Flask
- Cloudflare Static Assets for the JWorks frontend
- D1 binding `DB` for application data
- R2 binding `FILES` for attachments/documents
- OpenRouter key intended to be stored as a Cloudflare secret

## Important migration status
This repository is intentionally a **cloud migration foundation**, not yet the production replacement for JWorks 10.1.4 Windows.

The frontend and Cloudflare resource configuration are ready. `/api/health` tests the D1 binding. The full local Flask API still needs to be converted from Python `sqlite3`, filesystem uploads and Flask server sessions to D1/R2/cloud-compatible authentication. Unconverted API routes return an explicit 503 instead of silently losing data.

Keep using JWorks 10.1.4 Windows until the cloud API conversion is completed and tested.

## First Cloudflare setup
1. Create a D1 database named `jworks-db`.
2. Put its database ID into `wrangler.jsonc` in place of `REPLACE_WITH_D1_DATABASE_ID`.
3. Create an R2 bucket named `jworks-files`.
4. Apply `migrations/0001_initial_schema.sql` using D1 migrations.
5. Add `OPENROUTER_API_KEY` and `SECRET_KEY` as Cloudflare secrets when the API migration reaches those features.
6. Deploy the Worker.

The next guided setup step is creating/binding the D1 database in Cloudflare.
