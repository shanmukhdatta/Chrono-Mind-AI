# ChronoMind AI V2 — Permanent Implementation Tracker

**Canonical branch for the Phase 0 work:** `v2/phase0-safety`  
**Review PR:** [#1](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/1)  
**Last updated:** 2026-10-13  
**Rule:** never mark a phase complete without reproducible verification, explicit unresolved issues, and review approval.

## Master 14-phase roadmap

| Phase | Area | State | Exit criterion |
| --- | --- | --- | --- |
| 0 | Legacy repository audit, safety, security | IN PROGRESS | No known critical destructive/auth defects, tests, startup and local review |
| 1 | Modular development foundation, CI | IN PROGRESS | Reproducible environment, structured packages, automated gates |
| 2 | PostgreSQL, authentication, Firestore migration | NOT STARTED | Reconciled, reversible migration with account ownership |
| 3 | Tasks, recurrence and calendar | NOT STARTED | Full CRUD, recurrence exceptions and calendar integration |
| 4 | Goals, preferences and prioritization | NOT STARTED | Durable goal-task relationships and documented scoring |
| 5 | Constraint-based scheduling | NOT STARTED | No double bookings, deterministic constraint checks |
| 6 | LangGraph planning and replanning | NOT STARTED | Explainable plans, retries and deterministic fallback |
| 7 | Human approval, transactional execution and undo | NOT STARTED | Proposed vs committed separation and reversible changes |
| 8 | Structured AI assistant, model routing, voice | NOT STARTED | Validated tool execution and graceful outage mode |
| 9 | Personalization, focus and insights | NOT STARTED | Opt-in tracking and measurable transparent recommendations |
| 10 | Notifications and reliable background jobs | NOT STARTED | Exactly-once logical dispatch, retries and delivery policy |
| 11 | Complete responsive frontend | NOT STARTED | Integrated accessible flows on major screen sizes |
| 12 | AI evaluation, testing, security hardening | NOT STARTED | Evaluation evidence, threat model, load and failure tests |
| 13 | Deployment and demo | NOT STARTED | Staging sign-off, monitored production and recorded end-to-end demo |

## Five non-negotiable safeguards

1. **User-data control:** explicit deletion/export, consent, retention boundaries, tenant isolation, backups before migration.
2. **Concurrency and recovery:** persistent versions, idempotency keys, lease ownership, safe retries and transactional commits.
3. **Graceful LLM failures:** deterministic scheduling must survive provider outages, timeouts and malformed generations.
4. **Explicit notifications:** separate in-app record creation from actual push/email delivery; record success/failure and opt-in.
5. **Permanent progress records:** every phase records architecture decisions, changed files, tests, evidence, blockers and PR links.

## Phase workflow

1. Inspect the actual branch and diff, then record risks.
2. Write isolated patches with focused regressions.
3. Run fast tests, then integration, static and frontend build checks.
4. Compare actual behavior to acceptance criteria; record failures, never invent green results.
5. Update this tracker and the phase-specific audit; request manual review.
6. Only after review, merge intentionally; **never auto-deploy or auto-advance phases**.

## Current Phase 0 evidence

- Draft PR #1 started with removal of the destructive missed-task deletion.
- Fail-closed admin checks and Firebase bootstrap hardening added.
- Overlap-aware seven-day slot planner added.
- Daily Firestore transactional claim added around legacy scheduler.
- Strict CREATE/PATCH validation, task serialization and IST date handling addressed.
- Recurrence remains incomplete; the UI now calls this out as a rule preview.
- Pure slot-planner and schema regression tests were run on exact GitHub blob-matched local files: **19 passed**. GitHub Actions additionally confirmed **44 backend tests**, **22 focused tests**, Python compilation and frontend Vite production build on the code head.
- Full test-backed backend CI and frontend build passed. External Firebase/emulator verification and Antigravity browser startup still remain.
- See [Phase 0 Audit](PHASE0_AUDIT.md), [Development Guide](DEVELOPMENT.md), [Test Results](TEST_RESULTS.md), and [Migration Plan](V2_MIGRATION.md).

## Next milestone

Complete remaining live Firebase smoke tests and CI/frontend verification; resolve documented legacy concurrency gaps before marking Phase 0 done.

## Phase 1 in progress (2026-10-13)

- Started separate branch `v2/phase1-foundation` from the unmerged Phase 0 branch. **Do not merge Phase 0 or Phase 1 automatically.**
- Scope: shared configuration and lifecycle boundaries, local-date tests, CI quality gates, development documentation. See [Phase 1 implementation](PHASE1_IMPLEMENTATION.md).
- Acceptance is **pending** green final-head CI, external local startup/CRUD verification, and reviewer sign-off.
- Phase 0 remains IN PROGRESS and its Firebase/emulator/concurrency blockers are unchanged.
