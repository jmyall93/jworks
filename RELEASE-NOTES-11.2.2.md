# JWorks 11.2.2 — Two-Worker Cloudflare Build Layout

This release fixes the Cloudflare Workers Builds deployment conflict in 11.2/11.2.1.

## Architecture
- `jworks` remains the Git-connected Python Worker at the repository root.
- `jworks-ai` is now isolated under `ai-worker/` with its own Wrangler configuration.
- The root deploy command deploys only `jworks`; it no longer attempts to create/deploy a differently named Worker from the `jworks` CI build.
- `jworks` retains the `AI` service binding targeting `jworks-ai`.

## One-time Cloudflare setup
Create/connect a second Worker named `jworks-ai` to the same GitHub repository and configure that Worker to deploy using `npm run deploy:ai`. Add the `OPENROUTER_API_KEY` secret to the `jworks-ai` Worker. The main `jworks` Worker continues to deploy with `npm run deploy`.

## Retained 11.2 fixes
- Platform Owner navigation is hidden from customer-company sessions, with server-side authorization retained.
- Login microphone is anchored to the far right of login fields.
- Long company names in the SOW/report header are protected from clipping.
- AI traffic uses the JavaScript AI Worker through the internal service binding.

No D1 migration is added by 11.2.2.
