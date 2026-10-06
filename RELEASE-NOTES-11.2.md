# JWorks V11.2 — AI Service + Tenant UI Fixes

## What changed
- Added a dedicated JavaScript Cloudflare Worker (`jworks-ai`) for OpenRouter requests.
- The main Python JWorks Worker calls the AI Worker through a private Cloudflare service binding; the browser never receives the OpenRouter key.
- AI diagnostics now identify the JavaScript AI service separately from OpenRouter key/chat authentication.
- JWorks Owner navigation is hidden for every non-platform-owner session, with an additional client render guard; platform APIs remain protected server-side.
- Sign-in voice controls are initialized on the static login form and pinned to the far-right edge of supported fields.
- Scope of Work cover branding now reserves a protected right column for long company names so decorative cover artwork cannot clip the company name.
- Version updated to 11.2.

## Deployment
Run `npm run deploy` as usual. V11.2 first deploys the internal `jworks-ai` JavaScript Worker, then deploys the Python JWorks Worker with an `AI` service binding.

No D1 migration is required. Keep the existing `OPENROUTER_API_KEY` secret on the main `jworks` Worker; V11.2 passes it server-to-server through the private service binding for the JavaScript Worker to use on the OpenRouter request.
