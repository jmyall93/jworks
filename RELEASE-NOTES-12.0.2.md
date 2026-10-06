# JWorks V12.0.2

Deployment and mobile stabilization release.

- Fixed duplicate Flask `preferences_get` endpoint that blocked V12.0.1 deployment.
- Preserved legacy and V12 preference payloads through a single GET `/api/preferences` route.
- Added a real mobile public-site hamburger menu with Product, Solutions, Intelligence, Pricing, Knowledge Base, About, Support, Contact, Sign In and Start Free Trial.
- Fixed authenticated bottom navigation appearing while signed out on mobile.
- Improved public homepage phone layout, typography, cards, Project Pulse demo, footer and public sub-pages.
- Keeps existing D1 migrations; no new migration is required for V12.0.2.
