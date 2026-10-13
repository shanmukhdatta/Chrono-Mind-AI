# Phase 0 — Test Evidence

**Updated:** 2026-10-13  
**Reference branch:** `v2/phase0-safety`

## Executed in current development environment

| Command / scope | Result | Evidence |
| --- | --- | --- |
| `pytest -q tests/test_slot_planner.py` | **7 passed** | Exact source and test copies match GitHub blob SHA: `267b52772c6c45a6cdbdb76e8fbdea4868799c6c`, `aae2addb8b301abbd20e4c124940e4910cd7dbdb`. |
| `pytest -q tests/test_slot_planner.py tests/test_task_validation.py` | **19 passed** | Includes the above seven; task schema source SHA `0ba1d16ea5c941978ad4fcbafd1404768d83f3e8`, tests SHA `2790addb1febf30e2749b2b7c98216fefd3b761b`. Python runtime Pydantic 2.13.5, which differs from backend requirement 2.7.0. |
| Full backend `python -m pytest -q` on GitHub Actions | **44 passed, 1 warning** | [Run #38431087470](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38431087470), backend-smoke job, Python 3.11. |
| Frontend `npm ci && npm run build` on GitHub Actions | **PASS** | Same CI run; 2,286 modules transformed, Vite build succeeded. |
| Focused regression suite on GitHub Actions | **22 passed** | Includes the three original missed-task tests and 19 schema/planner tests. Same CI run; Python compilation passed. |
| Real Firebase auth or Firestore concurrency | **NOT RUN** | Requires configured test project/emulator. |
| Full authenticated API flow and visual UI | **NOT RUN** | Requires local backend/frontend and test credentials. |

**CI evidence:** [Run #38431087470](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38431087470), head commit `d8399dc73554538977e3c3b4d9d9e0f60cbd860f`, three jobs concluded success. Test output displayed above. A newer documentation-only commit should have CI rerun before merge.

Tests intentionally avoid destructive integration behavior on real personal task data.

## Approval rule

Do not mark Phase 0 complete, merge to main, or deploy until actual CI outcome plus Antigravity smoke tests have been recorded here.
