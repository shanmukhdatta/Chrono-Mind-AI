# ChronoMind implementation and handoff

## Assignment for the coding agent

Deliver an agentic personal planning assistant inside the existing ChronoMind V2 product. A user can describe a change, inspect a feasible proposal grounded in their own records, approve the exact edits, and see what actually changed. Take ownership of implementation, tests, fixes, commits and the final handoff. Work through the stages in dependency order without asking the owner to manage each stage. The scope is application engineering, evaluation and local verification. Cloud infrastructure, deployment and MLOps are separate projects.

**Repository:** https://github.com/shanmukhdatta/Chrono-Mind-AI  
**Reviewed base:** `main` at `ca8d8b7ddd4a93e292db014e3958faa84b813947`. Discover the current default branch and SHA at execution time. Reconcile subsequent changes before editing.

**Ready-to-send authorization**

> Implement the attached ChronoMind plan end to end in the linked repository. Use an isolated feature branch, preserve existing user changes, run and fix the relevant tests, and commit the verified changes locally. Continue through all in-scope stages without waiting for my approval between stages. Apply the product defaults in the plan. Give me the final branch, commit SHA, test evidence, demo steps and any genuinely blocked live checks. Leave push, merge and deployment for my separate approval.

If a remote handoff is wanted, the owner can add: “Also push your feature branch and open a draft PR against the default branch.” A local-only commit remains in the implementing agent's checkout. Use one implementing agent and one integration branch to avoid duplicate or conflicting deliveries.

## Product defaults

- V2 PostgreSQL is authoritative for this workflow. Firebase supplies identity. Preserve legacy Firestore routes, direct V2 forms, the public read-only sample and the legacy browser demo.
- Protect manual fixed commitments. A request naming a fixed event may propose changing that event. Show all affected work before approval. Proactive recovery may create a proposal and in-app alert.
- Treat prerequisites as blocking until completed. Explain blocked successors. Allocate only pending leaves and remaining effort. Preserve parent prerequisite constraints after decomposition.
- Respect hard dates, protected time, breaks and capacity first. Apply stated user priorities next, then prefer less disruption. Surface meaningful unresolved choices. Keep inferred focus-hour preferences soft and consented.
- Interpret preferences within the current request unless the user explicitly saves a lasting preference. A booked block, a finished focus timer and a completed task are three different outcomes.
- Prefer exact queries, one interpreter and the existing deterministic scheduler. Enable additional model roles selectively after evaluation. The core product must work with the provider unavailable.

## Stage 0 — establish working baselines

1. Inspect the actual checkout, instructions, route registration, migrations and existing CI commands. If no checkout is available, obtain the linked repository in the authorized workspace. Record starting SHA, branch and working-tree state. Isolate changes from the owner's work. Use disposable data and keep secrets out of fixtures and commits.
2. Read PR [45](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/45) and PR [46](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/46) at their current refs. At review time both were drafts; #46 was stacked on #45. Evaluate scheduler validation independently from its scoring objective. Reuse useful research retrieval patterns from #46 independently from six-specialist orchestration.
3. Run the existing backend, frontend, build, scheduler and disposable PostgreSQL checks using the repository's workflows as the executable reference. Record pre-existing failures separately. Exercise the actual route used by chat: the reviewed endpoint imported `llm_router.py`, while a routing test covered `model_router.py`.

**Acceptance:** baseline report includes exact revisions, executed checks, results, existing failures and scope of any missing credentials. Both legacy and V2 route families and both demos have compatibility coverage.

## Stage 1 — scoped tools, evidence and context

Build typed owner-bound tools for exact counts, paginated lists, entity search/read, dependencies, calendar ranges, limits, consented focus summaries, proposal history and inbox state. Share domain logic with the existing APIs. The server supplies the owner from authentication. Return evidence with source type, ID, field, version or fingerprint, observed time, zone, filters, completeness and pagination/truncation. Fix exact counts/list behavior in the actual assistant endpoint.

Resolve phrases against ID, active screen selection, titles, aliases, descriptions, dates and entity type. Keep an exam event distinct from its preparation task. Resolve local dates using the user's IANA zone and a request clock. Read overlapping time intervals by range. Omitted or truncated model context cannot establish that a whole day is free. Separate hard facts, inferred preferences, requested changes and observed outcomes.

**Acceptance:** fixtures with 47 pending tasks return 47 and paginate correctly; duplicate names trigger a targeted question only when needed; an unrelated owner's same-title record is never returned; partial calendar coverage prevents a definitive availability claim.

## Stage 2 — ship the complete one-task loop

Implement “Find 30 minutes tomorrow for my existing Control Systems revision task” through the real Assistant UI. Extend the planning service to accept a target task ID, requested minutes, date window and exact/flexible semantics. Current planning enumerates all pending leaves. Preserve the existing general preview entry point. Check remaining effort, indivisibility, session bounds, prerequisites and existing work. Render the relevant reason and the exact proposed block.

Persist the exact reviewed draft and its immutable revision/digest. Introduce idempotent request IDs and operation receipts. An authenticated human approves a particular revision. Under transaction locks, re-read the relevant facts, validate, write once and persist the receipt. Read the committed ID, owner, task and interval through a fresh calendar/domain query before reporting success. Clearly distinguish a durable commit awaiting verification from a failed write. Provide a working link back to the calendar or the confirmed block.

**Acceptance:** supported input creates one intended block after approval. Rejection creates none. Two clicks, a repeated start, a lost response after commit and a process restart cannot produce duplicates. A newly occupied slot conflicts cleanly. A read-back outage retries verification only. Verify with real disposable PostgreSQL and a UI flow with controlled identity/provider fixtures.

## Stage 3 — execution harness, edits and recovery

Extend the existing owner-scoped LangGraph/checkpoint and approval APIs. Store request/run IDs, resolved entities, bounded clarification state, source revisions, consent epoch where relevant, candidate IDs, proposal digest, step, budgets and receipt. Define awaiting clarification, awaiting approval, rejected, cancelled, stale, committed-unverified, verified and verification-conflict. Keep graph nodes replay-safe and release locks before model calls or human waits.

Make preview-to-save and preview-to-apply preserve the reviewed payload. In particular, unify the Tasks page decomposition apply behavior with the Assistant's exact-child confirmation. Version-check goal edits, destructive task drafts and affected calendar records as needed. Preserve older clients and pending proposal semantics with an explicit compatibility path and migration tests. Editing invalidates earlier confirmation. Guard undo by current block identity, provenance and before/after data. Verify all write paths share the locking/revision discipline required for their constraints.

**Acceptance:** two tabs cannot authorize an unseen edit; a confirmed decomposition keeps its reviewed titles and minute allocations; stale or cross-owner approval fails; cancellation before commit prevents the write; interrupted commits reconcile by receipt. PostgreSQL reconnect and inverse-operation tests pass.

## Stage 4 — scheduler and proactive correctness

Reuse `priority.py`, `planner.py`, `replanning.py` and `planning_api.py`. Factor shared preview/commit feasibility rules and independently check effort conservation, no overlap, permitted local work windows, splits, caps, breaks, release dates, deadlines, prerequisites and requested horizon. Use UTC for elapsed durations and local calendar boundaries for user intent. Clip cross-midnight work to the correct days. Evaluate #45's bounded task-order search against the existing baseline including long-task starvation, short-task bias and user-visible disruption. Document the objective selected.

Carry recurrence occurrence dates into earliest-start constraints. Preserve skip, deduplication, monthly and DST semantics. Keep parent constraints effective after decomposition. Test the actual apply entry points of `backend/scripts/propose_v2_replans.py` and `expand_v2_recurrence.py`; inspect the read-before-begin transaction paths and mixed missed/future tasks. Keep user-triggered and background proposal validation consistent.

**Acceptance:** independent invariant tests and deterministic fixtures pass on the production search path; an impossible case returns the unmet constraint and remaining minutes; future occurrences never start early; historical focus sessions never establish completion. Repeat worker apply tests on disposable data and verify intended deduplication/cooldown.

## Stage 5 — cross-feature replanning

Implement “My Control Systems exam moved to Friday; reorganize my week.” Resolve the named event, ask for missing time if material, gather complete commitments, task deadlines, goal links and preferences, then simulate the change without modifying calendar rows. Give each allowed operation a type, record ID, expected revision, before/after values and inverse. Support local event changes, adding blocks, and moving affected work blocks. Deadline changes require their own explicit diff. Unrelated protected commitments stay occupied.

Generate feasible candidates, compare with keeping the existing plan, and show displaced or unplaced work, reasons and exact differences. Commit a selected multi-record diff atomically. Use final-state validation so a legitimate relocation can free the space needed by the exam in the same transaction. Read back old and new intervals, check unrelated records in tests, and support guarded inverse updates.

**Acceptance:** one approval can move the named exam, relocate a conflicting project block and add a study session. Inject a new conflict or stale record on any operation: all three remain unapplied. After a successful commit, independently verify all three effects. Undo restores the old positions only if they are still valid and records match.

## Stage 6 — language, selective multi-agent reasoning and memory

| Component | Real job | Contract and boundary |
|---|---|---|
| Interpreter | Resolve ambiguous requests and produce typed intent | Input: utterance, local clock/zone, selected entity, narrow candidates and active clarification. Output: intent, IDs with evidence, operation fields, window, constraints, unresolved question and preference scope. Read and draft only. Validate schema and membership; ask one discriminating question as needed. |
| Tradeoff agent | Explain material differences between validated candidates | Input: feasible candidate IDs, measured differences and relevant preferences. Output: candidate ID or user-choice request, cited claims, tradeoffs and unmet goals. It cannot invent slots or change constraints. On failure present the deterministic comparison. |
| Application harness | Route, budget, checkpoint, verify permissions and effects | Direct dispatch for exact reads/forms. Parallelize independent reads once identity is resolved using a consistent snapshot. Then plan, validate, review, apply and verify sequentially. Only the authenticated domain writer can commit. |

Use one logical request path for text and editable voice transcription. Start with zero model calls for exact reads, one for ordinary language, up to two normal calls plus one schema repair for complex work. Initial interactive budget targets are 15 seconds of total model time and 6,000 input/1,200 output tokens per run; tune from measurements. Deduplicate effects and bound reads/retries. Treat retrieved notes, task titles and provider output as untrusted data.

Use exact SQL for dates, counts, calendar state and restrictions. Use owner-scoped lexical/full-text retrieval for task and goal descriptions and any explicitly saved notes/preferences. Cite source fields, versions, time and search coverage. When budget is tight, discard unrelated history and duplicate snippets before material facts. If a fact is missing, say which one. Compare embeddings only on a concrete paraphrase-retrieval failure; require improvement over lexical retrieval before introducing a vector index. Invalidate derived evidence on edit, deletion or consent revocation. Keep transient clarification, explicit lasting preference and opt-in behavior separate.

**Acceptance:** unsupported claims, fabricated IDs, record-level prompt injection, ambiguous references, missing facts and revoked consent have regression cases. Provider outage leaves forms, deterministic reads, preview and approval usable. Additional model calls are enabled by demonstrated benefit; document any capability retained as an evaluated experiment.

## Stage 7 — complete the product surfaces

| Surface | Required outcome |
|---|---|
| Tasks, goals, subtasks, dependencies | Existing CRUD/forms work; assistant drafts show cascade effects; hierarchy, versions, ownership and exact reviewed content are enforced. |
| Calendar, recurrence, preview, replan | Show fixed versus movable work, occurrence versus series, actual dates, hard conflicts, candidate differences and unplaced work. |
| Approvals, edits, undo, runs | Show exact revision, status, edit/reject/approve and verified effects. Resume by owner and receipt. Preserve history accurately. |
| Dashboard, briefing, notifications | Reuse exact aggregates, distinguish high priority from schedulable, use global unread count where applicable and distinguish a stored inbox item from delivery. |
| Focus, personalization, preferences | Use consistent sample windows for insights and scheduling. Show the sample size. Recheck consent, clear derived signals on opt-out and honor explicit overrides. |
| Chat and voice | Support clarification and the same evidence/approval flow for typed and dictated inputs. Let users correct transcripts. Provide text fallback. |
| Account and compatibility | Cover new records in export/deletion, disclose partial external cleanup, keep identity controls in Profile. Preserve V1 routes, demos and operator import boundaries. |

**Acceptance:** exercise real frontend entry points with realistic loading, empty, ambiguous, conflict, success and recovery states. Confirm new data respects export/deletion scope. Distinguish verified browser behavior from mocked provider, microphone or identity behavior.

## Repository map

- `frontend/src/pages/{AssistantV2,TasksV2,Goals,CalendarV2,PlanPreview,ApprovalCenter,AgentRunsV2,FocusV2,NotificationsV2,DashboardV2,PlanningSettings,Profile}.jsx` and `frontend/src/lib/`: reuse screens and client adapters, share diff/evidence/result components.
- `backend/v2/{api,assistant,llm_router,model_router,decomposition,calendar_api,dependencies_api,recurrence,focus_api,notifications_api,dashboard_api,account_data}.py`: reuse services and extract typed domain reads. Introduce evidence and agent contracts where justified.
- `backend/v2/{planning_api,priority,planner,replanning,proposals_api,agent_api,agent_graph,models}.py` and Alembic versions: snapshot, candidate generation, validated change set, receipt, checkpoint and read-back. Keep existing HTTP contracts compatible.
- `backend/tests/`, `frontend/src/lib/*.test.js`, `backend/evals/`, `evals/`: retain the existing suites; add coverage for new contracts, real entry points, failure injection and user-visible outcomes.

## Evaluation and final delivery

Compare current main, a single-model typed-tool baseline and the hybrid on paired frozen workspaces. Keep model family, tools, solver, budgets and fixture state identical for the baseline-versus-hybrid comparison where possible. Evaluate #45 separately on scheduler inputs and #46 on read-only research. Use simple, cross-feature, ambiguous, impossible, stale, missing-evidence, cross-owner, injected-instruction, timezone and interrupted-run cases. Include multiple seeds or repetitions for model variability and report sample sizes.

| Metric | Ground truth and proposed release criterion |
|---|---|
| Intent, entity, arguments | Hand-labeled acceptable intents and exact fixture IDs, dates and scopes. Target ≥95% resolvable-case accuracy and zero wrong-entity writes. |
| Retrieval and claims | Labeled necessary sources, exact SQL, field-level support and blind human review. Target ≥95% required-evidence recall, 100% exact-field correctness in release fixtures, zero cross-owner evidence. |
| Feasibility and effects | Independent constraint checker, small exhaustive cases, approved diff versus fresh database/calendar observations. Zero hard violations, unauthorized/duplicate effects or partially applied local changes. |
| Clarification and utility | Human labels for necessary versus avoidable questions; blind pairwise comparisons of materially different feasible plans. Initial target <5% unnecessary clarification and zero consequential guesses reaching commit. |
| Time and cost | Record p50/p95, calls, tokens and actual configured pricing per successful request including failed attempts; separate human wait. Zero model calls for exact reads. Gate the second role on meaningful quality gain at acceptable cost. |

Use deterministic checks for hard facts and side effects. Human reviewers judge preference fit and ambiguity. A calibrated LLM judge may assist semantic triage. If a human study or provider-enabled evaluation cannot run, deliver reproducible cases and report the missing evidence; keep speculative complexity off by default.

Extend existing non-content metrics and decision logs with run/step IDs, prompt/schema/model versions, tool names, redacted argument shapes, evidence revisions, latency, token usage, approval digest, receipt and verification outcome. Preserve complete replay fixtures for synthetic users. Limit ordinary user traces to necessary metadata with retention and deletion coverage.

**Final handoff must contain**

1. Starting and final SHA, branch, commit list and remote PR URL if authorized.
2. Feature-by-feature status and the specific workflow reachable through each relevant UI entry point.
3. Commands actually run and results for backend, frontend/build, disposable PostgreSQL, migrations, scheduler suites, browser flows and AI evaluations. Identify mocked, live, skipped and failed checks separately.
4. Two short reproducible demos: the one-task loop and the moved-exam loop, including a stale approval or lost-response recovery example.
5. Measured baseline-versus-hybrid results, remaining defects or external blockers, and the precise steps needed to reproduce any unverified live checks. Verify the committed tree and present a truthful final state.
