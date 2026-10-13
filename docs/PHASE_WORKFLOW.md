# ChronoMind AI V2 — Phase Development and Merge Protocol

## Ownership and phase sequence

This document is the canonical collaboration agreement for all subsequent ChronoMind V2 development chats.

1. **Assistant is responsible for implementation.** Inspect the current repository and roadmap, create a new `v2/phaseN-...` branch from the latest verified `main` after the previous phase is merged, implement complete phase-scoped backend/frontend code, add and update tests and documentation, and push a reviewable GitHub PR. Use connected GitHub tooling for code changes; report any permissions or execution limitations truthfully.
2. **GitHub Actions is the automatic testing bot.** `.github/workflows/phase1-quality.yml` is named `ChronoMind V2 CI` and runs for PRs into `main` or V2 integration branches, plus pushes to `v2/**`. It runs backend Python 3.11 tests/compilation, frontend Node 20 Vitest/build, and a tracked-file safety check. No secrets, production database or LLM calls are required for these checks. A successful CI workflow is not a substitute for real-service integration testing.
3. **Dependabot may create maintenance PRs.** It monitors GitHub Actions, backend pip and frontend npm dependencies weekly; updates are **never auto-merged**. Their checks and runtime impact are reviewed before acceptance.
4. **Assistant performs review and debugging.** Read failure logs, correct issues, push fixes, and verify all CI jobs on the **final exact commit**. If any job cannot run, report that rather than claiming success. Look for security, ownership, atomicity, data-loss and regression risks.
5. **Assistant supplies a copy-ready Antigravity prompt** for Windows local test startup, app/browser interaction, Firebase test environment, and any resource-heavy or external integration work that cannot be done through GitHub CI. Local checks must use dedicated test data and redact secrets. User returns the actual outputs.
6. **Assistant compares Antigravity evidence with acceptance criteria.** Disclose what passed, what failed, what was simulated, and what remains untested. Fix material regressions in the *same phase PR*, rerun CI and request Antigravity re-verification if needed. Maintain a permanent handoff and risk log.
7. **The user is the sole PR merge decision-maker.** Once phase-scoped code, GitHub CI and practical Antigravity validation are satisfactory, assistant explicitly says **"Ready for your merge"** and provides PR link, merge order and deferred risks. The assistant **does not merge the PR or deploy**. The user merges after their review.
8. **Begin the next phase only after verifying the merge into main.** Re-read architecture docs and the tracker, start from latest `main`, and retain unfinished safeguards on the roadmap. Do not restart or duplicate prior phases.

## Existing stacked PRs / immediate next action

- [Phase 0 PR #1](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/1) targets `main`.
- [Phase 1 PR #2](https://github.com/shanmukhdatta/Chrono-Mind-AI/pull/2) targets `v2/phase0-safety` while PR #1 is unmerged.
- When the user approves these development phases, merge **PR #1 first** using a **merge commit** to retain ancestry, then retarget **PR #2** to `main`, confirm the diff and required checks, and let the **user** merge PR #2. Avoid squash-merging PR #1 while PR #2 is stacked on its history.
- User approval for development merging does not mean automatic production deployment approval. The README lists a pre-existing Vercel/Render deployment; any automated release effects of merging `main` must be checked in those services. GitHub CI itself does not deploy.

## Phase acceptance gates vs production release gates

**A phase can be accepted** when its explicitly scoped implementation, tests, final-head GitHub CI, applicable local QA, documentation and review are satisfactory. Deferrable legacy flaws belong in the risk tracker with a named later phase, rather than automatically stopping every subsequent development phase.

**A phase must not be called complete** while critical defects within its own promised scope remain unresolved. Authentication isolation, backups before migration, non-destructive behavior and no secret leaks are never waived as "later" just because unit tests are green.

**A production rollout requires separate authorization**, recovery strategy, data safety, and deployment-specific verification. In particular:
- Legacy concurrent Firestore writes still have a read-before-write double-booking race; Phase 2 must model database integrity safely and Phase 5/7 must deliver and verify durable concurrency guarantees before the new scheduling engine is relied on.
- Real multi-worker Firestore transactions, expiring/revoking real Firebase tokens, browser Google OAuth interaction, optional-missed-task persistence and notification delivery require appropriately isolated integration tests.
- Account export/deletion, safe migration, LLM fallback and notification delivery semantics remain in the permanent 14-phase tracker.

## Before every user merge recommendation

Provide the PR link, final head SHA, exact GitHub Actions run URLs with results, Antigravity test summary with evidence boundaries, unresolved risks/next-phase owner, and whether any live deployment may be triggered. The user merges; the assistant checks resulting `main` before creating the next branch.
