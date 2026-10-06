# JWorks 10.2.3 Cloud

- Fixes first-administrator screen bootstrap.
- Cache-busts the application JavaScript so Cloudflare/browser service-worker caches cannot leave the old sign-in logic active.
- Makes startup DOM-ready safe.
- Cache-busts session/setup-needed startup requests.
- Preserves D1 cloud backend and Scope of Work Builder / Print to PDF workflow.
- No D1 migration required.
- wrangler.jsonc intentionally excluded so the deployed D1 database ID is not overwritten.
