# JWorks V11.2.4 — Secure JavaScript AI Transport

- OpenRouter key is read only from `env.OPENROUTER_API_KEY` inside `jworks-ai`.
- Main Python JWorks no longer reads or forwards the key.
- Browser never receives the key.
- Added jworks-ai diagnostics for secret presence and Authorization-header construction without exposing the credential.
- AI chat, connection test, and SOW generation share the JavaScript-owned transport.
- No D1 migration.
- Existing V11.2.x tenant/Owner Portal, microphone, and company-header fixes retained.

Required: `OPENROUTER_API_KEY` must be a Secret on `jworks-ai`. After this release is confirmed, the secret on main `jworks` is no longer required.
