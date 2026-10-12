# JWorks V13.3 — Testing Candidate / Import & Work Controls

## Changes
- My Work redesign: direct status and priority dropdowns, no misleading checkbox, clearer task/project/due metadata, filters and On Hold group.
- Project list: inline status changes for Upcoming / Active / On Hold / Completed; project progress remains visible.
- Excel task import: reads `Depends On`, `Assignee`, `Estimated Hours`; resolves predecessor links in a second pass; supports cross-project predecessor syntax `PROJECT-CODE::Task Name`; validates missing/ambiguous/self/circular dependencies; prevents import when validation errors exist; updates matching existing tasks instead of duplicating them.
- Import preview displays recognized predecessor count; import commit returns created, updated and linked counts.
- No database recreation or schema migration in this release.

## Limitations / required testing
- Dependencies currently support **one predecessor per task** (`depends_on`). Multiple predecessors and true multi-edge CPM require a separate schema and UI change.
- Task names must be unique within a project for deterministic import. To reference a task in another project use `PROJECT-CODE::Task Name` in `Depends On`.
- Existing tasks with the same project/name are updated. Import to a backup/test environment first, as import is not one atomic transaction.
- Circular dependency detection covers rows in the current import batch, not every possible cycle through previously existing tasks.
- Validate importer with a small sample before importing the full 227-task go-live plan. 212 predecessor links were expected in the plan; actual results must be checked against your workbook.
- Existing report schedules still need end-to-end runner/delivery testing.
- No production deployment or browser integration tests have been run here.
