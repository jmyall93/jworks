# JWorks 10.2.8 Cloud — Deterministic Deploy Pipeline

- Preserves the 10.2.7 root asset layout (`/app.js`, `/manifest.json`, `/sw.js`).
- Adds the known-good `wrangler.jsonc` with the real `jworks-db` D1 database ID.
- Contains no R2 / `FILES` binding.
- Deployment now runs `pywrangler sync` only to vendor Python dependencies.
- Removes any generated `.wrangler` deployment redirect before deployment.
- Runs `npx wrangler deploy --config wrangler.jsonc` directly so the checked-in config is the deployment source of truth.
- No D1 migration is required.

Cloudflare deploy command for this release: `npm run deploy`
