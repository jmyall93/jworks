# JWorks 14.2 — Project Workspace Polish

- Red/yellow/green outlines for project and task tiles based on overdue, blocked, approaching deadline, completed/on-track states.
- Refined project hero, metrics and board, with consolidated top actions and a single-row navigation (horizontal scroll on narrow displays).
- Daily Field Reports support persistent attachments (JPG/PNG/WebP/PDF/TXT, 1 MB each, 5 per report) stored in Cloudflare D1. Upload on submission, retry via report history, download via authenticated API.
- Requires running migration `0014_v14_2_field_report_files.sql` before deployment.
- Known limitations: no thumbnail previews, large file uploads, or R2 storage; attachments are stored as base64 in D1. Existing generic project attachment endpoints are not modified. Live browser/deployment validation still required.
