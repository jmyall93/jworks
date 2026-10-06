# JWorks V11.2.8 — SOW Document Control

- Editable SOW-specific Project Code; does not modify the underlying project code.
- Editable Revision label (supports 0/1/2 or A/B/C) and Revision Date.
- Revision History table with revision, date, description, and prepared-by fields.
- Removed the internal “Bid / Work Document” warning from contractor-facing print/PDF output.
- [TO CONFIRM] remains available while drafting, but JWorks blocks Approved for Bid / Issued / Awarded documents while unresolved markers remain.
- AI drafting prompt explicitly treats [TO CONFIRM] as an internal drafting marker that must be resolved before issue.
- New D1 migration 0006 adds SOW document-control fields. Existing SOWs remain intact and fall back to their project code / revision 0.
- Retains the working V11.2.7 AI architecture and OpenRouter auth diagnostics.
