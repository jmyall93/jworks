# JWorks V13.5 — Customizable Analytics Dashboard

- REYLEX ID / OIDC intentionally deferred; existing authentication unchanged.
- Colorful Command Center with 10 selectable analytics widgets, donut/bar/line/KPI views where applicable.
- Per-user, per-company browser-local saved layout, widget order, width, and graph types.
- Project filtering; metrics computed from existing JWorks data, no mock data.
- No D1 migrations, no server endpoint changes, no task deletion or import actions.

## Limitations
- Dashboard preferences are stored in localStorage on the current browser; they do not yet synchronize across devices.
- Due-date chart is a bucket comparison, not a historical time series. Budget widget displays configured estimated project budgets, not actual spend.
- Authentication and V13.4 task reconciliation need separate live integration tests.
- This is a testing candidate; validate on a staging Worker before production.
