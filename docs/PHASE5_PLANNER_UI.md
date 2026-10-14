# Schedule preview page

An authenticated `/planning` route renders real output from the deterministic PostgreSQL-backed preview API.

Features: horizon selection, read-only time blocks, timezone-local display, summary totals, unscheduled explanations, true error states and explicit no-write status. There is intentionally no misleading 'Apply' action until durable human-approval and conflict-safe transactional execution exist.

Stacked dependency: backend preview PR #12, which depends on #11, #10 and #9. Local browser + database smoke test required before merge.
