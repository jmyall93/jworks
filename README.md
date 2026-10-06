# JWorks 10.2.2 Cloud

Cloudflare Workers + D1 edition, based on JWorks 10.1.4 Fresh Start.

## Included in 10.2.1
- D1-backed first administrator setup, login, logout, secure cookie sessions and CSRF protection.
- Core cloud CRUD for projects, tasks, checklists, milestones, costs, risks/issues, inbox, meetings, changes, decisions, procurement and field reports.
- Scope of Work Builder inside every project.
  - Manual structured scope creation.
  - AI-generated contractor-ready first drafts through OpenRouter.
  - Hybrid editing: AI draft remains fully editable; sections can be added, removed, edited and reordered.
  - Contractor/staff print layout with browser Print / Save as PDF.
  - Draft / Internal Review / Approved for Bid / Issued / Awarded status.
- Project-only Gantt and editable AI task-plan UI from 10.1.4 are retained.
- R2/file attachments remain intentionally disabled.

## Existing Cloudflare deployment upgrade
1. In Cloudflare D1 > jworks-db > Console, run `migrations/0002_cloud_auth_sow.sql` once.
2. Upload/commit this release to the existing GitHub `jworks` repository.
3. Cloudflare should redeploy automatically. Deploy command remains `uv run pywrangler deploy`.
4. Open JWorks. Because the database is fresh, the login screen should change to **Create administrator**. Create the first account with any non-empty password.

## AI Scope generation
Manual and hybrid SOW editing work without an AI key. To generate AI drafts, add a Cloudflare Worker secret named `OPENROUTER_API_KEY` containing your OpenRouter API key. Never commit the key to GitHub.

## PDF output
Open a scope and choose **Print / Save PDF**. JWorks opens a clean Letter-size contractor document and invokes the browser print dialog. Choose **Save as PDF** to create the bid-package PDF, or choose a printer for a paper copy.

## Current migration boundary
10.2.1 converts authentication plus the most important project/task and SOW workflows. Some older advanced endpoints (templates, report revisions, baselines, full AI Project Builder, attachments, etc.) still return a clear cloud-migration message until converted. Keep the 10.1.4 Windows build as the fallback copy while cloud migration continues.
