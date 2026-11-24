# Planning audit and implemented alternative — 2026-11-24

Base reviewed: ca8d8b7ddd4a93e292db014e3958faa84b813947.
Scope: V2 planning, priority/context matching, and offline evaluation. This is
not a certification that every screen, external service, or deployment works.

## Findings and changes

| Finding | Implemented correction |
|---|---|
| Only three handcrafted rank variants were considered | Bounded task-order insertion search, at most 32 unique candidates, beam width 4 |
| “Deadline first” added a constant bonus without sorting deadlines | Actual earliest-deadline seed order, passed intact to the placement engine |
| Priority times minutes rewarded long tasks disproportionately | Sum of priority times the fraction of each task scheduled; exact rational comparison |
| Validator omitted conservation, breaks, work windows, horizon, caps and indivisible work | These constraints now independently checked before selecting a candidate |
| Overlapping imported work was counted repeatedly | Union occupied work intervals before calculating daily usage; round partial occupied minutes up |
| Wall-clock arithmetic could misstate duration across DST | Allocate and measure elapsed time in UTC, derive daily boundaries in the user's timezone |
| Substring matching treated “art” as related to “cartography” | Require shared complete tokens or exact normalized phrases |
| Invalid deadlines could fail during sorting; duplicate IDs conflated work | Validate task identifiers, effort and aware deadlines before ranking |
| Evaluation exercised only baseline placement and dropped some task fields | Add production-search mode and preserve priority, splittability and work occupancy inputs |

The existing planning API already calls choose_schedule; the new search is
therefore on the proposal path, not an unused demonstration module. No new paid
API, model download, database migration, or dependency is introduced.

## What the algorithm does

Generate priority, earliest-deadline and shortest-job seeds, evaluate unique
orders, then explore insertion neighbors from the best four evaluated orders.
Neighborhood moves are restricted to the first 12 positions of each order.
Every candidate uses the existing feasible slot allocator. Keep the highest
importance-weighted task-progress score; ties prefer more minutes and fewer
blocks. Decision traces disclose the method, objective and search budget.

This replaces the three-strategy-only selection, not all deterministic rules.
Importance scores remain a transparent cold-start heuristic. Deadlines, fixed
events, consent, ownership and approval must remain enforced constraints.
It is not reinforcement learning, a trained preference model, CP-SAT, or a
proof of global optimality.

Objective tradeoff: normalized progress can favor short tasks over one large
task. This is an explicit product choice, not an empirically proven preference.
Task splitting/granularity can affect the objective. Validate acceptance and
long-task starvation before adopting it broadly.

## Alternatives and next work

| Alternative | Role and requirements | Status |
|---|---|---|
| Bounded search | Improves selection without training data or a solver dependency | Implemented in this branch |
| OR-Tools CP-SAT | Jointly choose start times and orders with no-overlap, capacity and precedence constraints; add a solve-time budget and benchmark against this baseline | Recommended next if placement failures persist; not implemented |
| Learned ranking | Replace handcrafted soft priority weights using consented acceptance, edits, completion and missed-session outcomes; validate on held-out users/time periods | No trained model claimed |
| Contextual bandit | Rank feasible alternatives using context and observed reward; log chosen actions and selection probabilities for offline evaluation | Requires deliberate instrumentation and exploration design |
| LLM planner | Interpret goals and extract structured requests; keep independent schedule validation | Do not use an unconstrained LLM as the feasibility authority |

Primary references consulted:

- [Google OR-Tools job-shop scheduling](https://developers.google.com/optimization/scheduling/job_shop): interval scheduling with precedence and no-overlap constraints.
- [Vowpal Wabbit contextual-bandit tutorial](https://vowpalwabbit.org/docs/vowpal_wabbit/python/latest/tutorials/python_Contextual_bandits_and_Vowpal_Wabbit.html): contextual decisions and feedback for chosen actions.

## Verification

Local environment has Python 3.9.6, no pytest, no Node and no direct GitHub DNS.
Source was read through the connected GitHub API. Domain checks run locally;
the existing GitHub Actions workflow supplies Python 3.11, dependencies, frontend
build/tests and PostgreSQL integration.

- Ten new unittest regression methods pass, including 60 seeded randomized
  workloads with feasibility, input immutability, deterministic repeatability,
  candidate-budget and baseline-objective comparisons.
- Eight existing pure planner/replanner test functions pass via direct invocation.
- Production candidate-search evaluation: 120/120 existing scenarios pass.
- CI now runs both baseline and production-search scenario modes.
- Initial CI found a timestamp-representation compatibility regression. Preview
  output now retains the user's local timezone while arithmetic remains UTC;
  a dedicated regression test preserves this contract.
- Final GitHub CI status must be checked on the pushed commit; see the PR.

The randomized comparison proves only the tested invariants and non-regression
under the newly selected objective. The 120 scenarios are synthetic and many
are variations of a small number of templates. Neither is user-outcome evidence.

## Remaining limitations and practical acceptance

Search still uses greedy slot placement, 90-minute session limits, the current
focus-hour heuristic and handcrafted importance scores. Dependencies remain
blocked until prerequisites are recorded complete; this does not jointly plan
an unfinished prerequisite chain. Existing future blocks are not moved.
No learning quality, production latency, real OAuth, model-provider response,
notification delivery or multi-user browser behavior was measured locally.
Nonexistent/ambiguous DST preference boundaries retain ZoneInfo's default
resolution and need an explicit product policy for users selecting those hours.

Before merging/deploying, use an isolated test account:

1. Install backend requirements with Python 3.11, run all pytest tests, and both
   python -m v2.evaluation commands (with and without --optimized).
2. Run npm ci, npm test and npm run build in frontend.
3. Create a 60-minute urgent task due in one hour and a higher-priority task due
   later. Confirm the preview fits both where feasible.
4. Add fixed events and work limits; approve a proposal and verify the calendar,
   reload persistence, undo, and stale-proposal rejection.
5. Verify another account cannot read or approve those proposals.
6. Check focus consent off/on, actual assistant credentials, timezone display,
   and notification delivery. Record errors and response timings without secrets.

Confidence: 0.90 in the tested domain fixes; end-to-end production readiness
remains unverified. The user retains merge/deployment control.
