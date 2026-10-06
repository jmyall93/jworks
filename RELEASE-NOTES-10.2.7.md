# JWorks 10.2.7 Cloud — Root Asset Routing Fix

- Moves browser assets out of `/static/` and serves them at the public root:
  - `/app.js`
  - `/manifest.json`
  - `/sw.js`
- Updates `index.html` and service-worker references to the new root paths.
- Removes the old `public/static` directory to eliminate duplicate/stale routes.
- Preserves the 10.2.6 API/D1 backend and first-administrator bootstrap.
- No D1 migration is required.
- `wrangler.jsonc` is intentionally not included; keep the repository's working D1 configuration and `run_worker_first: ["/api/*"]` setting.
