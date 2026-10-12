# JWorks V13.4 — Task Reconciliation Testing Candidate

## Changes
- Duplicate Task Inspector: company-scoped duplicate groups with task IDs, dates, status, linked task/checklist/attachment counts.
- Guarded exact-duplicate deletion: explicitly choose keep/delete; refuses records with linked data, mismatched task fields or stable external IDs. Does not automatically delete or merge ambiguous records.
- Dependencies Only XLSX workflow: validates project/task names and lets the user choose exact target/predecessor IDs where duplicates exist. No new tasks; preserves task status, dates, assignments and notes. Validates cycles before atomic D1 batch update.
- Stable external task IDs: migration 0013 adds `external_import_id`. The dependency-only importer can read `Task ID` or `External Task ID` if supplied in an XLSX file. Existing spreadsheets without these columns can still use explicit ID selection. External IDs are assigned only when supplied; existing duplicates cannot be automatically disambiguated without user selection.

## Safety and limitations
- Back up the remote D1 database before deployment and before reconciliation.
- The duplicate inspector does not automatically merge records with different data or linked objects. Those must be reviewed manually.
- The current task schema supports one predecessor per task, not a many-to-many dependency graph.
- Do not re-run the old full task import to repair dependencies; use the new Dependencies Only section.
- Browser/Cloudflare integration tests have NOT been run. Validate with fictional tasks in a test environment first.
- Migration `0013_v13_4_task_reconciliation.sql` is additive; never recreate D1.
