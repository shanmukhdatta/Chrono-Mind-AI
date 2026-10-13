# Phase 0 — Test Evidence

**Updated:** 2026-10-13  
**Reference branch:** `v2/phase0-safety`

## Executed in current development environment

| Command / scope | Result | Evidence |
| --- | --- | --- |
| `pytest -q tests/test_slot_planner.py` | **7 passed** | Exact source and test copies match GitHub blob SHA: `267b52772c6c45a6cdbdb76e8fbdea4868799c6c`, `aae2addb8b301abbd20e4c124940e4910cd7dbdb`. |
| `pytest -q tests/test_slot_planner.py tests/test_task_validation.py` | **19 passed** | Includes the above seven; task schema source SHA `0ba1d16ea5c941978ad4fcbafd1404768d83f3e8`, tests SHA `2790addb1febf30e2749b2b7c98216fefd3b761b`. Python runtime Pydantic 2.13.5, which differs from backend requirement 2.7.0. |
| Full backend `pytest` | **NOT RUN** | Firebase Admin, LangGraph, APScheduler, and Groq not available in current execution runtime. |
| Frontend `npm ci && npm run build` | **NOT RUN** | Complete frontend source and dependencies not mounted locally. |
| Real Firebase auth or Firestore concurrency | **NOT RUN** | Requires configured test project/emulator. |
| Full authenticated API flow and visual UI | **NOT RUN** | Requires local backend/frontend and test credentials. |

Use `.github/workflows/phase0-validation.yml` for full CI verification. Check actual GitHub Actions conclusions; a committed workflow is **not evidence that it passed**.

Tests intentionally avoid destructive integration behavior on real personal task data.

## Approval rule

Do not mark Phase 0 complete, merge to main, or deploy until actual CI outcome plus Antigravity smoke tests have been recorded here.
