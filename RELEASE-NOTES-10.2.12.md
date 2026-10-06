# JWorks 10.2.12 Cloud — AI & Administration Fix

- Fixed Administration remaining on “Loading system status…” / “Checking…”.
- Added cloud-aware D1 system status.
- Added OpenRouter configuration status without exposing the API key.
- Added Test AI Connection from Administration and AI Settings.
- Replaced obsolete local API-key editor with Cloudflare-secret-aware AI Settings.
- SOW AI now uses `openrouter/free` and returns useful sanitized provider errors.
- Added OpenRouter app headers and safer response parsing.
- No database migration required.
- Existing authentication, D1 data, SOW UI/report redesign, and deterministic deployment are preserved.
