# JWorks v13.8 — Navigation & Workspace Refinement

## Implemented
- Simplified navigation: configurable pinned primary destinations, Explore tools, Settings/Support, and Administration.
- Collapsible desktop navigation with saved per-user preferences.
- Settings rebuilt with consistent tabs, readable spacing and properly stacked form controls.
- Removed nested legacy Settings page and repeated headings.
- Added navigation personalization and grouped feature visibility.
- Feature toggles update navigation immediately; project detail sections and tabs use the same visibility preferences where identifiable.
- Existing dashboard controls, data, backend, calendar, knowledge base and support tickets retained.

## Limitations / validation
- Preferences remain browser-local; cross-device synchronization is not implemented.
- Feature visibility is presentation-only, not an access control. Some advanced screens and modal fields may not yet obey every toggle; verify against actual workflows.
- JavaScript syntax validated; live browser and deployment verification still required.
