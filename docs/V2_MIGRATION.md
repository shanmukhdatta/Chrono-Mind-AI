# V2 Firestore → PostgreSQL Migration Strategy (Phase 2)

> **Historical proposal.** The statement below that no migration scripts exist is no longer current: V2 Alembic schema migrations now exist through revision `0013_focus_context`. **Live Firestore cutover has still not been verified or executed as part of this finalization.** See [SETUP_V2.md](SETUP_V2.md).


This is a proposal, **not an executed migration**. Phase 0 must not alter or delete live Firestore documents.

## Scope and ownership

- Authentication remains Firebase Auth initially; PostgreSQL users link to verified Firebase `uid`.
- Entities: user settings, tasks, recurrence definitions/occurrences, calendars, notifications, goals, proposed plans and audit history as introduced by subsequent phases.
- Tenant isolation: every user-scoped row includes an owner identifier; server-side checks and database constraints protect cross-user access.
- Preserve original Firestore document IDs as legacy external IDs for deduplication and audit.
- Timestamp policy: store instants as UTC-aware values; store event local date/time plus IANA timezone separately. Do not guess timezone for ambiguous historical records.
- Preserve `completed`, `completed_at`, `rescheduled`, `rescheduled_from`, and recurrence strings exactly in an archive.

## Safe migration sequence

1. Inventory schema variants and all user subcollections, including malformed dates and sparse legacy records.
2. Export and back up Firestore in a secure location with access controls; record counts/checksums. Define rollback owner.
3. Design PostgreSQL schema, constraints, foreign keys, recurrence model, indexes and ownership rules; review migration scripts.
4. Run a **dry run on anonymized/test data**, calculating rejects and compatibility mapping before any production action.
5. Backfill in small idempotent batches keyed by `(firebase_uid, legacy_document_id)`, with checkpoint and audit trail.
6. Reconcile counts and sampled field-level hashes; verify user separation, timezone conversion, recurrence lineage and deleted-state policy.
7. Use a controlled dual-read/dual-write or short maintenance window with explicit reconciliation, depending on architecture.
8. Enable read cutover only after shadow comparison and authorized review, with feature flag and tested rollback.
9. Keep Firestore read-only archive temporarily under a documented retention policy; never delete source automatically.
10. Validate exports, deletion requests, recovery and restore drills before concluding Phase 2.

## Explicit blockers

- No current PostgreSQL migration scripts or production database provisioned.
- Legacy recurrence instances may not exist despite stored rules.
- Current task CRUD conflict checks are not atomic.
- Legacy history lacks stable timezone and event version metadata.
- Consent, retention and recovery controls require design and user review.
