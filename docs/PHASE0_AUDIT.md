# Phase 0 — Source Audit, Fixes, Remaining Risks

Updated 2026-10-13. Scope: actual `v2/phase0-safety` branch. **Not a production-readiness declaration.**

| # | Audit item | Source finding and current status |
| --- | --- | --- |
| 1 | Missed-task safety | Previous PR removed silent task deletion; regression tests preserved. Pure policy reviewed, not yet Firebase integration tested. |
| 2 | Admin auth | PATCHED: missing/placeholder `ADMIN_UID` denies access; valid Firebase UID required; sensitive verifier messages not exposed. |
| 3 | Firebase startup and verification | PATCHED: authenticate after explicit Firebase Admin initialization, with revoked-token check. Real credentials/emulator verification outstanding. |
| 4 | Scheduling overlap | PATCHED algorithm: on each proposed placement, immediately reserve time and use cached occupied intervals; final writes recheck live occupancy. |
| 5 | Skipped day and date arithmetic | PATCHED: search tomorrow through six days after tomorrow, local `Asia/Kolkata` business date; frontend uses local date, not UTC split. |
| 6 | Duplicate worker jobs | PATCHED: Firestore transactional daily run claim with eight-hour lease and owner token. Emulator concurrency tests outstanding. |
| 7 | API validation, serialization and timezones | PATCHED: strict task schema/PATCH validation, 15-minute minimum, date-only overlap checks, UTC ISO timestamp output, date range/query validation. |
| 8 | Recurrence | BROKEN/INCOMPLETE: helper `generate_recurring_instances` exists but no create/update route invokes it; series editing, conflict handling, future generation are absent. UI explicitly labels recurrence as a preview. Phase 3 implementation required. |
| 9 | Backend and frontend startup | Documented in DEVELOPMENT.md. Environment-specific startup not run with real secrets here. |
| 10 | Automated tests | 19 pure regression tests passed against exact blob-matched sources; GitHub Actions subsequently confirmed 44 backend tests, 22 focused tests and frontend build (run #38431087470). |
| 11 | Remaining bugs + migration | Documented here and in V2_MIGRATION.md. |
| 12 | Persistent tracking | V2_IMPLEMENTATION_TRACKER.md, TEST_RESULTS.md, development and migration guides created. |

## Remaining material risks

- **Non-transactional user task writes:** conflict query then set/update is still a race with concurrent API writers. Phase 5/7 must use transactional per-user/day locking or versioned acceptance. Rollover read-before-write is not an atomic guarantee.
- **Legacy scheduler lease expiry:** a worker holding a claim for over eight hours could overlap an eventual reclaim. Production V2 must heartbeat, enforce ownership fencing or adopt a durable singleton queue. Current behavior is a protective interim fix.
- **Legacy missed-task timing:** a 23:55 IST job moves unfinished work before the calendar day ends; this behavior is preserved to avoid unexpected schedule changes. Confirm policy with product owner in Phase 10.
- **AI actions:** legacy assistant may execute a model-suggested create_task without an explicit user approval. Phase 7/8 must add propose→confirm→commit and schema-constrained tools. Do not assume output is trustworthy.
- **Recurrence:** storage only; no reliable automatic generation, exclusions, edits-to-series or duplicate prevention.
- **Data deletion:** legacy bulk account deletion is irreversible and not backed up; future export/retention/deletion workflows need dedicated consent and audit.
- **Notification guarantees:** in-app Firestore records are not proof of device/email delivery, and retries may duplicate notifications after partial failures.
- **Firestore query indexes:** multi-field calendar range queries may require indexes not bundled here. Check emulator and deployment indexes.
- **Credential availability:** Firebase service account and Groq credentials are user-provisioned and must never be committed.
- **Database migration:** no PostgreSQL changes should occur in Phase 0.

## Required safety gates before Phase 0 approval

- [x] Full Python dependency installation and `pytest` suite green on GitHub Actions (44 passed).
- [x] Frontend `npm ci && npm run build` green on GitHub Actions.
- [ ] Startup: backend /health and frontend dev server.
- [ ] Live/emulator Firebase auth: valid, invalid, expired, revoked token and missing admin UID.
- [ ] Emulator concurrent tasks and multi-worker nightly lease claim.
- [ ] Calendar POST, GET, PATCH date-only change, completion and notifications smoke tests.
- [ ] Regression audit that optional missed tasks remain persisted.
- [ ] Document remaining concurrency limitations and obtain explicit reviewer sign-off.

Do not merge PR #1 into main until gates and release impact are reviewed.
