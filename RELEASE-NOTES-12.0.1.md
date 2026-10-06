# JWorks 12.0.1 — Stabilization & Commercial Site

- Repairs Settings with D1-backed per-user preferences.
- Repairs Company Portal and persists branding, feature flags, support email, document branding and inactivity timeout.
- Adds automatic first-login What's New modal for 12.0.1 with Explore/Skip actions.
- Adds 10-minute default inactivity sign-out with a 60-second warning.
- Adds optional support email delivery through the existing `jworks-ai` service binding and Resend. Configure `RESEND_API_KEY` and optionally `SUPPORT_FROM_EMAIL` on `jworks-ai`, then set the destination in Company Portal.
- Replaces public demo examples with fictional, industry-neutral projects.
- Expands the public Intelligence story around practical AI and automation workflows.
- Adds distinctive Product, Solutions, Intelligence, Pricing, About, Knowledge Base, Support, Contact, Privacy and Terms experiences.
- Adds public contact inquiry persistence and optional email notification.
- Refreshes service-worker cache/versioning to 12.0.1.

## Database
Apply `migrations/0008_v12_0_1_stabilization.sql` to the existing `jworks-db`. Do not recreate D1.

## Email
Email is optional. On `jworks-ai`, add a Resend API key as the `RESEND_API_KEY` secret. Set `SUPPORT_FROM_EMAIL` to a verified sender address/domain. In JWorks Company Portal, set the support notification destination. Tickets are still saved if email is not configured or delivery fails.

## Legal drafts
Privacy and Terms are product-launch drafts, not legal advice. Obtain qualified legal review before accepting paying customers.
