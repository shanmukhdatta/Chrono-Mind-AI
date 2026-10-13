# Phase 1 — Antigravity Windows QA intake

**Evidence:** user-provided Antigravity QA execution report dated 2026-10-13. This file records externally reported results, not tests run by the GitHub environment.

## Reported local environment

Windows 11 AMD64, Python 3.11.9, Node 25.9.0, npm 11.12.1. The canonical CI remains Python 3.11 and Node 20.

## Reported successful checks

- 60/60 Python tests and bytecode compilation.
- 3/3 Vitest tests and frontend production build.
- HTTP 200 from FastAPI `/health` and Vite development server.
- Authenticated test Firebase login and task POST, duplicate-time conflict (409), GET, PATCH, completion, stats, DELETE, deletion confirmation, and date-range query (11/11 operations according to the QA report).
- The legacy nightly scheduler was disabled for local testing.

## Finding: composite index requirements

The live test initially encountered a Firestore `FailedPrecondition` due to an equality filter on `date` combined with secondary `order_by(start_time)`. The Antigravity environment reportedly modified `backend/services/task_service.py` locally, but that patch was **not in the upstream Phase 1 branch** at intake.

The upstream fix is now separately implemented with explicit query shapes:

- Single-day list: Firestore `where(date == selected_day)` using an automatic single-field index, followed by local stable ordering.
- Date range: Firestore date-bounded range ordered by date only, followed by local stable `(date, start_time, task_id)` ordering.
- Unfiltered list retains the previous server-side single-field start-time ordering.
- Query-recorder tests verify no new composite requirement is introduced for these endpoints.

No broad Firestore fallback reads, production index deployment, data migration or unbounded full-collection scan was added for day/range retrieval. Large date-range reads remain a legacy pagination/limits concern for future phases. The updated committed code still needs live Firebase retesting.

## Remaining unknowns

- The report did **not** establish actual browser UI interaction via Playwright; HTTP probes and builds are not a browser functional test.
- No emulator multi-worker lease tests, simultaneous competing task writers, token revocation/expiry integration tests, or real notification delivery tests were reported.
- No security credentials, test user identifiers or raw tokens are included here.
- PR approval and merging are still pending. **Neither Phase 0 nor Phase 1 is signed off.**
