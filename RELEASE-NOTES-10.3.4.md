# JWorks 10.3.4 — OpenRouter Request Fix

- Rebuilds the OpenRouter call around an explicit Cloudflare Workers `Request` object.
- Attaches `authorization` directly to the exact Request object sent to `workers.fetch`.
- AI diagnostics now verify that Authorization exists on that outbound Request object before transmission.
- Uses manual redirect handling so credentials cannot be silently forwarded to another host.
- Preserves all 10.3.3 personalization, Report Studio, mobile/PWA, microphone, and light-theme fixes.
- No D1 migration required.
