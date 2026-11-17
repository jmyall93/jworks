# JWorks v13.6 — Adaptive Workspace

Built on the supplied v13.5 testing package.

## Added
- Settings → Dashboard: widget selection, order, width, chart/list/summary presentation, dashboard metric strip toggle and layout presets.
- Dashboard no longer has a Customize Dashboard button. A single selected widget expands across the available dashboard width.
- Graphs are optional per widget; List and Summary displays are supported.
- Settings → My features: personal feature visibility preferences.
- Project → More → Customize project view: per-project section visibility preferences.
- Settings layout refresh: more whitespace, less dense panels, responsive navigation and form layouts.
- Search input fixes: project search updates results without replacing the input; task search restores focus and caret; global search updates results in place.

## Important limitations
- New adaptive preferences are stored per company/user in the browser's localStorage. They do not yet synchronize between devices.
- Feature hiding is presentation-only; it does not revoke server-side permissions or delete data.
- Project section visibility covers mapped tabs and the health strip; some deeply embedded advanced panels may still need additional mapping.
- This package passed Python syntax compilation and JavaScript syntax checking, but has not been tested against a deployed Cloudflare environment or real customer accounts.

## Deploy
Use the existing README and Wrangler instructions. Preserve your Cloudflare bindings, secrets, and database. Back up the current deployment first.
