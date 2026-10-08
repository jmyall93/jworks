# JWorks V13.2 — Testing Candidate

This release freezes end-user feature growth and begins the official testing stage.

## Owner control plane
- `JWORKS-OWNER` now opens a dedicated JWorks Administration shell rather than the customer project workspace.
- Platform Overview with company/user/project/task/report/support metrics.
- Company administration for plan, seats, status, support configuration and inactivity policy.
- Cross-company user visibility and company-scoped user/role management.
- Per-company feature overrides stored in company configuration rather than source-code edits.
- Platform configuration for customer defaults and controlled platform feature flags.
- Owner-level audit log foundation and System/testing page.
- Existing customer Company Portal remains unchanged for customer administrators.

## Architecture boundary
Business planning, marketing planning, CRM/commercial metrics and cross-product Owner HQ are intentionally **not** added to JWorks. Those belong in the future Reylex/Jelix parent-company platform. JWorks Administration is the control plane for the JWorks SaaS product only.

## Testing rule
No new end-user features during the testing stage. Findings should be classified as Broken, Confusing, Annoying or Missing; Missing has the highest bar.
