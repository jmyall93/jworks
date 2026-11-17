# JWorks v13.7 — Settings, Calendar and Support Center corrections

- Fixed Settings navigation stretching vertically because inherited sidebar styles were affecting its nested navigation.
- Replaced the calendar with a seven-column responsive month grid with a three-item daily preview and clickable full-day schedule.
- Removed the question mark prefix from Support Center navigation.
- Added 16 searchable, clickable Knowledge Base guides with step-by-step content.
- Added Support Center tabs for Knowledge Base, Submit issue, and My tickets.
- Existing ticket submission persists tickets to the Cloudflare-backed support_tickets table.
- Added company-scoped ticket detail API and a ticket detail modal.
- Tickets show status, priority, subject, date, and description. Status is updated by the support team; customer-side status editing is intentionally not available.

## Limitations
- No automatic support-agent response workflow or customer email updates were added. Existing optional email notification remains dependent on service configuration.
- Changes were syntax-checked, not browser-tested against live Cloudflare services.
- Preserve existing D1 bindings, secrets, and database. Back up before deployment.
