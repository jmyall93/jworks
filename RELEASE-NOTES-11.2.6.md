# JWorks V11.2.6 — OpenRouter Literal Fetch Fix

- Built directly from the verified V11.2.5 package.
- Replaced the AI Worker outbound OpenRouter request with the literal native JavaScript `fetch()` shape documented by OpenRouter.
- Removed the `Headers` object from the outbound OpenRouter call.
- Normalizes accidental surrounding quotes or a pasted `Bearer ` prefix in the Cloudflare secret.
- Adds safe diagnostics for OpenRouter key format, key length, and outbound header style without exposing the key.
- No D1 migration.
- No tenant, UI, SOW, project, or database changes.
