# JWorks 10.3.1

## Focused fixes
- Rebuilt OpenRouter authentication request using native JavaScript `Headers` and `RequestInit` objects so the Cloudflare Python/Pyodide FFI does not drop the Authorization header.
- All existing AI features continue to use the shared `openrouter_chat()` path.
- Replaced visible **Dictate** buttons with compact microphone icons embedded inside supported text inputs and text areas.
- Listening state is shown on the microphone icon without adding extra field clutter.
- Preserves JWorks 10.3 mobile/PWA, Settings, users, custom reports, SOW, D1 and Cloudflare deployment architecture.

No new D1 migration is required for this release.
