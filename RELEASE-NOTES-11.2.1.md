# JWorks V11.2.1 — Cloudflare Multi-Worker Deploy Fix

## Fix
- Corrects the V11.2 Cloudflare Workers Builds failure where the CI system forced the auxiliary `jworks-ai` deployment to use the connected Worker name `jworks`.
- The AI deployment step now temporarily removes Cloudflare Workers Builds' `WRANGLER_CI_OVERRIDE_NAME` only for the `jworks-ai` deploy.
- The main JWorks deployment remains connected to and deployed as `jworks`.
- Keeps the `AI` service binding pointed at `jworks-ai`.

## Retained from V11.2
- JavaScript OpenRouter proxy architecture.
- Platform Owner navigation hidden from customer-company users, with backend authorization enforcement.
- Login microphone anchored to the far-right of the input.
- Responsive company/SOW branding header fix for long company names.
- Existing D1 data and migrations unchanged.

## Deployment
Use the existing Cloudflare deploy command:

```
npm run deploy
```

No new D1 database or migration is required.
