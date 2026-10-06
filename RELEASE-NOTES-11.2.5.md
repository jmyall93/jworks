# JWorks V11.2.5 — AI Worker Credential Isolation

Built from the complete V11.2.3 release.

- `jworks-ai` now owns `OPENROUTER_API_KEY` and reads it directly from its own Cloudflare environment.
- Main Python `jworks` Worker no longer reads or forwards the OpenRouter credential.
- Added `/diagnostics` inside the JavaScript AI Worker. It reports only booleans: Worker reached, secret detected, secret non-empty, and Authorization header present.
- OpenRouter key test and chat use the exact same JavaScript-created Authorization headers.
- AI SOW generation now uses the same secure service-binding path without a Python-side key check.
- Updated Test AI Connection UI to show the actual AI Worker state rather than the main Python Worker secret state.
- No D1 migration. Existing company/project data is unchanged.

## Required Cloudflare setting
`OPENROUTER_API_KEY` must exist as a Secret on the `jworks-ai` Worker in the environment being deployed.
