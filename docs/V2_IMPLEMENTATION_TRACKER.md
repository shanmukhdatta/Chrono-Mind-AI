# ChronoMind AI V2 — Permanent Implementation Tracker

> **Archived phase-tracker snapshot.** Dates and phase states below are historical and may predate merged V2 features. The canonical resumption checklist is [FINAL_HANDOFF.md](FINAL_HANDOFF.md); current source navigation is [FEATURE_MAP.md](FEATURE_MAP.md).


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

**Phase 1 initial CI evidence:** both jobs passed on commit `f1844556`: backend 59 passed, frontend 3 passed, Vite build passed. [Push workflow](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38441356503) · [PR workflow](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38441410275). The final branch head, local test-account smoke checks, and review remain outstanding. No status promotion.

**2026-10-13 external QA intake:** Windows Antigravity reported successful 60-test Python suite, 3-test frontend suite, both local servers and 11 authenticated Firebase task operations. A composite-index query failure was discovered; the local fix was not pushed. The Phase 1 branch adds an independently audited single-index query shape plus regression tests. See [PHASE1_QA_REPORT.md](PHASE1_QA_REPORT.md). Do not infer distributed concurrency or browser automation completion.

## Phase 1 latest verification and review gate (2026-10-13)

- Exact upstream implementation SHA: `96f256a29f541b9bb44148969e0304b4d745462f`.
- GitHub [push](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38443760055) and [PR](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38443766957) quality workflows: **success**; **63 backend tests**, **3 frontend tests**, compilation and Vite production build passed.
- Second Antigravity report: verified clean fast-forward, preserved stash, **63 local backend**, **3 frontend**, working /health and Firebase authenticated task lifecycle, with day/range queries now free of the earlier composite-index failure. Treat this as **externally reported live integration evidence**, not GitHub CI Firebase coverage.
- Browser UI interaction is unverified (Playwright driver download failed); human Chrome/Edge login/calendar inspection remains an acceptance action.
- Phase 0's bad/revoked/expired token, multi-worker lease, simultaneous task-write, notification and non-destructive missed-task integration tests remain unverified. Those safeguards **must not** be inferred from successful CRUD or regression tests.
- PR [#1](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/1) and PR [#2](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/2) remain in review. Phase 1 is **IN PROGRESS / AWAITING REVIEW**, not complete. No merge or deployment.

## Phase 1 deep verification intake (2026-10-13)

- Antigravity isolated harness reported expected missing/invalid/expired/revoked token responses; missing/mismatched administrator rejected; owner-only nightly job claim with **in-memory doubles**; optional missed-task candidate preservation; and notification writes only for apparently committed moves.
- **Do not equate harness outcomes with real expired/revoked Firebase tokens, simultaneous cross-process Firestore transactions or actual notification delivery.** Live concurrent task writes and distributed lease tests are unverified. The TOCTOU task-write race is still present.
- Browser guidance was provided, but interactive browser execution has not been verified.
- Phase 1 cleanup removes **16 tracked Python bytecode files** and ensures subsequent compilation does not dirty Git; adds a CI guard and permanent simulated token-error branch tests.
- A test password appeared in the external QA transcript. No credential is copied into Git; rotate it before reuse.
- Maintain Phase 0 and Phase 1 as **IN PROGRESS / awaiting reviewer acceptance**. Do not merge/deploy/start Phase 2.

**Manual UI checklist corrected:** frontend authentication is Google OAuth popup; the Antigravity email/password browser guide does not match the source. See [PHASE1_BROWSER_QA.md](PHASE1_BROWSER_QA.md). Checklist is PENDING actual interaction evidence.

## Persistent development protocol — user approval (2026-10-14)

The user owns PR merging. The assistant must implement phase-scoped code on GitHub, run/verify the automatic GitHub Actions CI bot, debug failures, and supply an exact Antigravity Windows verification prompt. After receiving satisfactory local evidence, the assistant explicitly recommends whether the user should merge, including remaining limitations. **The assistant must never merge a PR or auto-deploy under this agreement.** The user merges; the assistant checks `main` before beginning the next phase.

See [PHASE_WORKFLOW.md](PHASE_WORKFLOW.md). The Phase 1 quality workflow is generalized to **ChronoMind V2 CI** for subsequent `v2/**` phases, with Python/Node tests and a tracked-file hygiene guard. Dependabot may propose weekly backend/frontend/workflow maintenance PRs; nothing auto-merges.

Current stack: Phase 0 PR #1 -> `main`, Phase 1 PR #2 -> `v2/phase0-safety`. The user should merge #1 first (merge commit), then Phase 1 #2 can be retargeted to `main`. Both must preserve explicit known risks and may affect existing Vercel/Render production deployments if those services track `main`.

## New work: Phase 2 PostgreSQL foundation branch (2026-10-14)

- Phase 0/1 branches were merged into main. The old tracker paragraphs above are historical records, not current PR state.
- Development branch: `v2/phase2-postgres-core`; **do not merge until CI and Antigravity checks**.
- Added SQLAlchemy domain tables, Alembic revision, tenant-scoped V2 goals/tasks/preferences API with optimistic task versions, and isolated API tests.
- Existing Firestore endpoints and data remain untouched. PostgreSQL cutover/export/import, live database smoke tests, and full Phase 2 acceptance are **not complete**.
- See [PostgreSQL Core](PHASE2_POSTGRES_CORE.md) for setup and limitations. Never claim Phase 2 completed solely on the basis of this foundation.

## V2 integration snapshot — 2026-10-14

- Feature branches are **stacked draft PRs #9–#34**, targeted at their previous feature branch, not directly at main. None were merged into main as part of this implementation sequence.
- Latest integrated work: PostgreSQL domain, secure goals/tasks/preferences, fixed events, conflict-aware deterministic schedule previews, human approvals and undo, durable LangGraph graph foundation, structured assistant drafts and voice frontend, task/focus/dashboards, opt-in behavior preferences, recurrence, notifications, cross-user data export and task dependency DAG.
- GitHub Actions passed for the preceding branches through #33; PR #34 and the integration branch must be rechecked against their latest commits.
- **No real PostgreSQL/Firebase/Microphone/LLM or production end-to-end verification was performed by this development session.** GitHub CI exercises isolated tests and frontend build, not live external services.
- Firestore V1 remains the deployed/legacy data source until controlled migration. Do not delete existing users/tasks and do not claim complete V2 deployment.
- A portable route-registration and Alembic revision-chain test plus an Antigravity manual integration handoff are added in the final integration branch.
- Real PostgreSQL migrations, PostgreSQL checkpointer recovery, owner isolation with live Firebase identities, all-user/data deletion, managed cron, full task dependency sequencing, CI E2E, mobile/a11y and launch hardening remain release blockers.
- **Next operator action:** run [V2 Antigravity integration acceptance](V2_ANTIGRAVITY_HANDOFF.md) on a local disposable database and return evidence; merge only after resolving failures and reviewing stacked PR order.
