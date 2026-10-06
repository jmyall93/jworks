# JWorks 10.2.6 Cloud — Selective Asset Routing

This release isolates API traffic from frontend asset traffic.

## Required Cloudflare routing change
In the existing `wrangler.jsonc`, preserve the real D1 database ID and change only:

`"run_worker_first": true`

to:

`"run_worker_first": ["/api/*"]`

Optionally add `"not_found_handling": "single-page-application"` inside the `assets` object.

This makes `/api/*` execute the Python/Flask Worker first while `/static/*` and other frontend files are served directly by Cloudflare Static Assets.

No D1 migration is required. `wrangler.jsonc` is intentionally not included because the repository copy contains the real D1 database ID.
