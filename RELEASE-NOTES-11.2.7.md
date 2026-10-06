# JWorks V11.2.7 — OpenRouter Egress/Auth Probe

- Based directly on the complete V11.2.6 release.
- Adds a server-side OpenRouter authentication probe inside `jworks-ai`.
- Tests four request-construction methods against `GET https://openrouter.ai/api/v1/key`:
  1. literal headers object
  2. `Headers` object
  3. explicit `Request` object
  4. lowercase `authorization` header
- Each probe records only method, HTTP status, redirect flag, response URL, and provider error. The API key is never returned or logged.
- Uses `redirect: manual` so redirects cannot hide where authentication changes.
- Updates optional OpenRouter app attribution header to current `X-OpenRouter-Title` spelling.
- Chat continues to use native JavaScript `fetch()` with the API key held only by the `jworks-ai` Worker.
- No D1 migration and no tenant/project/UI feature changes.
