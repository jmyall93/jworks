# JWorks v14.0 — Project Workspace Redesign (Testing)

- Redesigned Daily Field Report form with clear sections, improved layout and existing save endpoint.
- Consolidated Status Report, Report Builder and Save Snapshot into one Reports action.
- Rebuilt Project Gantt with dated bars, milestones, progress, zoom controls and today marker. No timeline drag-to-edit in this release.
- Redesigned My Work and Projects with search that retains focus, focused views and 35-item paging.
- Project Work tab uses a more readable task list; full search remains in My Work.
- No database schema changes. Existing data and APIs preserved.

## Testing limitations

- Browser interaction and Cloudflare deployment have not been verified.
- Field report attachments and PDF export are not included.
- Project Work tab shows up to 75 tasks; use My Work for the full list.
- Reports menu reuses existing report functions and should be checked against live data.
