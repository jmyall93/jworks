# JWorks 10.2.11 Cloud — Scope of Work Builder & Report Redesign

## What changed
- Rebuilt the Scope of Work section editor into a wide, responsive document-editing layout.
- Heading and content fields no longer collide; content editors are full-width and auto-grow as text is entered.
- Added clearer section numbering, live heading labels, compact move/remove controls, and a sticky save/preview action bar.
- Rebuilt the Scope of Work print/PDF output as a contractor-ready document with a JWorks cover, project metadata, revision/status blocks, numbered sections, highlighted `[TO CONFIRM]` markers, document-control approval area, and print-friendly Letter formatting.
- Print now opens as a preview first instead of immediately forcing the browser print dialog.
- Fixed the AI Scope loading-state DOM target while working in the SOW module.
- Updated frontend/service-worker cache identifiers to 10.2.11.

## Cloud foundation
No database migration is required. Authentication, D1 bindings, root asset routing, and the deterministic `npm run deploy` pipeline are unchanged.
