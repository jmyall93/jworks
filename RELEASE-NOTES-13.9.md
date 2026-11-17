# JWorks v13.9 — Workspace Reliability & UI Polish

## Changes
- Sidebar uses JW monogram when collapsed, preventing clipped logo.
- Owner tools separated from customer Administration; Implementation Center remains owner-only.
- Additional project tab/section visibility checks for personal feature preferences.
- Company Portal form fields receive responsive stacked styling and improved spacing.
- What's New replaced by searchable release history compiled from included release notes.
- Implementation Center shows an error/retry state if its API fails.

## Important limitations
- Feature visibility is UI-only, not authorization. Some legacy forms and dialogs still need explicit integration and testing.
- Implementation Center requires platform_owner role and a working /api/implementations backend.
- Release notes reflect the packaged changelog, not independently verified deployed features.
- Live browser and Cloudflare testing were not performed.
