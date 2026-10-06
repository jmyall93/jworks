# JWorks V11.0 — Company Platform Foundation

V11 turns JWorks from a single-workspace project app into the foundation of a multi-company platform.

## New
- JWorks Platform Owner portal for customer-company administration.
- Company records with generated Company IDs, status, plan and licensed seat counts.
- Company Portal for organization profile, user seats, roles and branding.
- Roles: Platform Owner, Company Administrator, Manager / Project Manager, User and Viewer foundation.
- Login now requires Company ID + username + password.
- 14-day self-service trial signup with five seats and generated Company ID.
- Forgot-password token foundation. Email delivery is intentionally not faked and remains unconfigured until a transactional email provider is connected.
- Company logo, address/contact and report footer settings.
- Company branding injected into Project Reports and Scope of Work print/PDF output, with JWorks attribution retained.
- Company seat enforcement when administrators add active users.
- Company subscription records and statuses for future billing integration.
- Existing users are migrated into `My JWorks Workspace`; the original administrator becomes the JWorks Platform Owner. Existing owner workspace Company ID is `JWORKS-OWNER`.
- Company members can see project/state records created by active users in their company. Core project/task edit/delete authorization now recognizes company membership.

## Database
Migration `0005_v11_multicompany.sql` adds companies, memberships, subscriptions and password-reset tokens while preserving existing data.

## Important foundation notes
- Billing/payment collection is not connected yet; subscriptions and seat limits are administered inside JWorks.
- Password reset email delivery is not connected yet.
- Company logos are stored as compact image data in D1 for this first V11 foundation release; UI limits uploads to 500 KB. A future storage release should move logos/documents to object storage.
- Existing project tables still retain creator `owner_id`; V11 layers company membership over that model to preserve existing data. A future migration can add explicit `company_id` columns to every tenant-owned table for stricter database-level tenancy.
- OpenRouter diagnostics/fixes from 10.3.5 are retained; the unresolved provider authentication issue is not represented as fixed in V11.
