# Cloud migration status

## Ready
- GitHub-safe repository layout
- JWorks 10.1.4 frontend carried forward
- Cloudflare Python Worker entrypoint
- Static Assets routing
- D1 database binding definition
- R2 storage binding definition
- Initial D1 schema (26 tables)
- Health endpoint
- Secrets/data excluded from Git

## Still to convert before production
- Login/setup/session/CSRF authentication
- Project/task/checklist/milestone CRUD
- Dashboard refresh payload
- Attachments and document revisions -> R2
- AI settings/chat/task-plan API -> Cloudflare secret + OpenRouter
- Reports, templates, approvals, decisions, procurement, field reports
- Backup/export strategy for D1/R2
- End-to-end browser testing

The 10.1.4 Windows build remains the production-safe version until these are complete.
