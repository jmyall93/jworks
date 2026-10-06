# JWorks 10.2.9 Cloud

## Administrator setup diagnostics and rollback
- Preserves the working 10.2.8 deployment/static-asset architecture.
- Reworks `/api/setup` into explicit stages: user-state check, password hashing, D1 user insert, and session creation.
- Returns a useful JSON `stage` and `detail` when Cloudflare/Python/D1 fails instead of an opaque HTTP 500.
- Rolls back a newly inserted administrator if session creation fails, preventing a half-created account from locking first-run setup.
- No D1 migration required.
