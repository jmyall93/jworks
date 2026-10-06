# JWorks V11.2.3

## AI response handoff fix
- Keeps the V11.2.2 two-Worker Cloudflare architecture.
- Reads the JavaScript service-binding response with `Response.json()` through the Python Workers FFI instead of converting `Response.text()` through `str()`.
- Normalizes successful OpenRouter chat responses in `jworks-ai` with explicit `content`, `model`, authentication, and HTTP status fields.
- Treats HTTP 200 from `/api/v1/key` as an authenticated success when OpenRouter reports `ok`.
- Adds a specific error when OpenRouter returns HTTP 200 without a readable assistant message.
- Diagnostic version bumped to 11.2.3.

No D1 migration is required. Both Cloudflare Workers continue to use the same GitHub repository; `jworks-ai` deploys from `ai-worker/wrangler.jsonc`.
