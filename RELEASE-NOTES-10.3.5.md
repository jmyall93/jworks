# JWorks 10.3.5 — Direct Python Workers Fetch

## OpenRouter transport change
- Replaces the 10.3.4 JavaScript `Request`/`Headers` construction path with Cloudflare Python Workers SDK `fetch()` directly.
- Sends the OpenRouter request with `fetch(url, method="POST", headers={...}, body=...)`, matching Cloudflare's documented Python syntax.
- Keeps `OPENROUTER_API_KEY` server-side and never returns or logs its value.
- All JWorks AI features continue to use the same shared `openrouter_chat()` provider path.
- AI diagnostics now identify the transport as `workers.fetch(url, method, headers, body)` and confirm that headers were passed directly.

## Other
- No D1 migration.
- No R2 binding.
- Preserves the JWorks 10.3.4 application and 10.3.3 light-theme improvements.
- Service-worker cache bumped to `jworks-v10.3.5-shell`.
