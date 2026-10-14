# Explicit V1 Firestore -> V2 PostgreSQL task backfill

**This branch does not migrate anyone's data automatically.** The operator must run the script, review dry-run counts, confirm a restricted-access Firestore backup, and opt into PostgreSQL writes. Firestore is read-only throughout.

Single-user dry run:
```powershell
cd backend
python -m scripts.import_firestore_tasks --uid YOUR_VERIFIED_FIREBASE_UID --timezone Asia/Kolkata
```
After verifying the Firestore backup, initializing a local PostgreSQL database, running Alembic, and reconciling counts:
```powershell
$env:CHRONOMIND_APPROVED_MIGRATION='1'
python -m scripts.import_firestore_tasks --uid YOUR_VERIFIED_FIREBASE_UID --timezone Asia/Kolkata --apply --backup-confirmed
```

Existing source `date`, `start_time`, and `end_time` map to a task and calendar session using the operator-specified IANA timezone. They do NOT become inferred deadlines. Completion and importance are retained. Raw records are archived per user with SHA-256 checksum in `v2_legacy_task_archive`. If old records overlap, both logical tasks survive but only the first free session is placed; other imported tasks stay unscheduled and are counted. Repeated import skips existing `(owner_uid, legacy_id)` pairs. Invalid records block the whole user import; private manual review is required.

**Limitations / blockers:** This command needs real Firebase Admin read access and DB permissions, explicit user scope, matching timezone assumption, a verified full backup and a reconciliation/rollback plan. User-profile, notifications, recurrence exceptions and other Firestore subcollections are NOT imported here. The backfill is not full production cutover; legacy storage must remain intact until manual acceptance.
