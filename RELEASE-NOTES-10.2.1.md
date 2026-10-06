# JWorks 10.2.1 Cloud

This is the first functional cloud application release after the 10.2 deployment foundation.

### Cloud backend
- First-admin setup stored in D1.
- PBKDF2-SHA256 password hashing with per-password salt.
- D1-backed 7-day secure HttpOnly sessions.
- CSRF token validation for authenticated changes.
- Core project/task and common project-record APIs moved from local SQLite patterns to D1.

### Scope of Work Builder
Each project now has a **Scope of Work** tab. Create a manual scope, request an AI first draft, or start with AI and edit everything yourself. Sections can be added, deleted and reordered. Scopes have lifecycle status and are stored per project in D1.

The AI prompt is deliberately instructed not to invent site facts and to mark unknown requirements as `[TO CONFIRM]`.

### PDF / print
Every scope has **Print / PDF**. It produces a clean Letter-size bid document and opens the browser print dialog, where the document can be printed or saved as PDF.

### Still pending
R2 attachments are disabled. Several legacy advanced APIs are still being converted. This release is intended to establish a secure working cloud core and the new SOW workflow.
