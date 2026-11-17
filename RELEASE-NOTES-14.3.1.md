# JWorks v14.3.1 — Mobile Navigation & Project Toolbar Correction

- Restores Notes as the fifth mobile bottom-navigation destination (Home, Projects, My Work, Notes, More).
- Moves project back navigation to a breadcrumb above the project header.
- Makes Task, Reports, Schedule, and Edit the primary project actions.
- Replaces the large More Actions button with a compact ellipsis menu for remaining project operations.
- Removes duplicate Edit Project and Project Settings entries; both now use the existing Edit Project form.
- Adds small-screen grid layout for the primary project actions and five equal-width mobile navigation slots.
- Keeps the existing v14.2 field-report attachment API and database migration unchanged.

## Verification / limitations
JavaScript syntax and archive integrity are checked. This package has not been browser-tested or deployed to Cloudflare. The app's legacy pages still need comprehensive real-device responsive testing. Backup and test on staging first.
