# ChronoMind AI V2 — README-to-code audit

> **Historical feature audit (14 October 2026).** Many gaps listed below were subsequently addressed in PR #43 or the V2 finalization PR. Do not treat this older matrix as current implementation status. Use [FEATURE_MAP.md](FEATURE_MAP.md) and [FINAL_HANDOFF.md](FINAL_HANDOFF.md) instead.


**Audit date:** 2026-10-14. **Reviewed branch:** `v2/readme-completion-and-release-fixes`, based on merged `main`. The original V2 architecture README remains a **product specification**, not proof of completed functionality. This audit distinguishes source-code presence from live verification.

## Capability matrix

| README architecture requirement | Current implementation | Status |
|---|---|---|
| Firebase authentication / tenant authorization | Legacy auth and V2 UID-scoped endpoints | Code + isolated tests; live verification pending |
| PostgreSQL domain / Alembic migrations | Eleven ordered migrations, logical tasks distinct from blocks | Code + CI; live Postgres migration pending |
| Task/goal CRUD with goals, importance and deadlines | V2 Tasks, Goals screens and endpoints | Code + CI; live end-to-end pending |
| Fixed commitments / calendars | PostgreSQL CRUD, overlap guard, V2 daily calendar | Code + CI; month/week V2 views missing |
| Recurring series | Daily and weekly, skips, bounded materialization | Partial: no general RRULE/monthly or automated renewal |
| Task dependencies | User-owned acyclic prerequisite DAG; blocked reasons | Partial: no within-one-plan joint scheduling |
| Dynamic priority scoring | Importance, deadline, active goal and explanations | Partial: no postponement count, context switching, flexibility or full behavior feedback |
| Deterministic scheduling | Fixed events, time windows, daily caps, basic 90min splitting, preferences | Implemented heuristic; not a full optimization/constraint-quality pipeline |
| Missed-task recovery | Past unfinished sessions can generate fresh suggestions | Manual preview; no event-triggered V2 automatic replanning |
| Bounded replanning | At most three validation/extended-horizon tries inside LangGraph | Partial: bounded candidate ranking and horizon retries, but no full constraint optimizer |
| Semantic task decomposition | Bounded session splitting and explicit non-splittable task flag; no semantic subtask tree | **Missing semantic decomposition** |
| Approval, rejection, undo | Transactional PostgreSQL proposals and review UI | Code + isolated tests; real concurrency verification pending |
| User modification of proposed plan | Pending plan sessions can be moved individually with full revalidation and audit; no bulk plan-editor | Partial |
| Durable LangGraph | Checkpointed planner, bounded horizon retries, human interrupt and Agent Runs page | Partial: external database restart not verified; no full graph quality optimization |
| Structured assistant | Validated task/goal drafts plus human-confirmed task update/complete/archive/delete actions | Partial: goal editing, richer querying, proactive plan tools and complete tool workflows missing |
| Adaptive LLM routing | Basic no-LLM query shortcut, allowlisted fast/reasoning selector and token/latency logs | Partial: heuristic routing only, no full cost dashboard or multi-provider fallback |
| Voice | Browser STT and languages where browser supports | Implemented option; real browser/device acceptance pending |
| Behavioral learning | Opt-in focus records, preferred-hour heuristic applied to preview | Partial: no postponement/approval acceptance feedback or category-specific profile |
| Explainability / decision history | Priority explanations, persisted proposal decisions and before/after audit history | Partial: no complete rationale for every planner decision |
| Token/latency/cost observability | Per-user latency/token data in PostgreSQL and user-scoped metrics API; optional operator-configured cost rates | Partial: no full LangSmith tracing or end-to-end cost analysis |
| AI evaluation | Two deterministic scheduling regression datasets (120 scenarios each) and invariant checks | Partial: no full agent/LLM benchmark, fairness/stats or 100 human-validated intent cases |
| Notification service | Persistent in-app deadline notifications and manual worker | Partial: no managed deployment job / push / email |
| Firestore → PostgreSQL | Dry-run import of legacy tasks, idempotent with archive | Partial: no full source coverage, reconciled cutover or backup validation |
| Account export/deletion | V2 PostgreSQL data export; legacy deletion explicitly scoped | Partial: no comprehensive cross-store deletion |
| Complete responsive frontend | Multiple separate V2 pages + legacy V1 views | Partial: V2 month/week calendar and TypeScript migration missing |
| Startup/CI | Github Actions backend + frontend; guarded V2 launch configuration | Code + CI; real database, credentials and hosting pending |
| Production deploy | Existing legacy Render/Vercel configs; V2 config placeholders | **Not deployed/verified as V2** |

### What is intentionally NOT in core V2

The README explicitly classifies Kafka, microservices, Kubernetes, Redis, full reinforcement learning, pgvector semantic memory, multi-agent orchestration, and external calendar import as **future extensions**. These are not mandatory for the prototype and must not be described as shipped.

## Concrete release risks

1. Browser startup: AppShell referenced `Bell` without importing it (fixed in this audit branch).
2. Browser preflight: FastAPI CORS omitted `PUT` despite V2 preference/event APIs needing it (fixed).
3. Default route opened the old Firestore dashboard, not V2; new opt-in `VITE_V2_DEFAULT=true` directs signed-in users to the V2 dashboard and hides legacy navigation (fixed, **disabled unless configured**).
4. Missed task: pending work with only old scheduled sessions was treated as already planned; the scheduler now permits explicit fresh proposals for that unfinished work (fixed; automated nightly recovery still absent).
5. Database liveness: default health endpoint does not check V2 DB; `/health/v2` now tests actual PostgreSQL connectivity (fixed).
6. PostgreSQL and LangGraph durability are not tested on a real database by existing CI, and React build success does not prove browser runtime behavior (still requires local tests).
7. Legacy Firestore fake-success demo API bypass remains in V1. V2 pages do not fabricate persisted records; a true single-storage cutover is not done.

## Release status

**Not ready to call 'every README feature implemented' or production deployed.**

The integrated branch is a **substantial testable V2 candidate**, not a certified finished app. GitHub unit/build CI should be checked against the final audit commit; it cannot replace live PostgreSQL, Firebase, browser and multiworker verification. Use `docs/V2_ANTIGRAVITY_HANDOFF.md` to run the integrated tests and verify application behavior. Do not merge into main or replace production V1 until the remaining release blockers are accepted or resolved.

### Merge strategy

This consolidated PR targets `main` and includes all V2 changes already developed in draft PRs #9–#35 plus additional release corrections. It is a **single alternative review path**. Do not merge both this PR and all stacked PRs; pick one strategy to avoid duplicate review/conflicts. Preserve the stacked PRs as historical review records, or close them after successful consolidated merge.

## Reconciliation notes — Oct 14, 2026

The original stacked PR chain #9–#35 is already incorporated by merged PR #37. The divergent draft #36 contained further hardening but could not safely merge over main. A clean main-based branch and PR #39 selectively bring forward its four additional Alembic migrations, versioned task safety controls, bounded alternative planning, assistant usage metrics and user-visible planning decision history. The same branch adds constraint-checked proposed-session movement. Older stacked drafts should be closed rather than merged again.

**Remaining functional gaps:** semantic subtask decomposition and approval UI, proactive missed-task plan proposals on a managed schedule, complete assistant tool coverage (update/complete/delete/query with approval), monthly/advanced recurrence, V2 week/month calendar, full user-account deletion across Firestore/PostgreSQL/checkpoints, comprehensive migration and consistency validation, production job orchestration, live authentication/database concurrency tests, cross-device speech QA, monitoring and full production deployment.
