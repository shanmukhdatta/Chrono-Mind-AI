"""Operator-only, read-only source Firestore migration.

Requires explicit one-user scope and verified backup acknowledgement:
  cd backend
  python -m scripts.import_firestore_tasks --uid FIREBASE_UID
  CHRONOMIND_APPROVED_MIGRATION=1 python -m scripts.import_firestore_tasks --uid FIREBASE_UID --apply --backup-confirmed

No source Firestore writes/deletes. Prints only counts, never task titles.
"""
import argparse
import os
import sys
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.firebase_service import get_db
from v2.db import engine
from v2.legacy_import import convert_legacy_task, import_converted
from v2.models import User


def main():
    parser = argparse.ArgumentParser(description="One-user V1 Firestore task import")
    parser.add_argument("--uid", required=True, help="Verified Firebase UID")
    parser.add_argument("--timezone", default="Asia/Kolkata", help="Explicit legacy local IANA timezone")
    parser.add_argument("--apply", action="store_true", help="Write only to PostgreSQL")
    parser.add_argument("--backup-confirmed", action="store_true", help="Operator attests secure Firestore export exists")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile source Firestore tasks against imported PostgreSQL records")
    args = parser.parse_args()
    if args.apply and (
        not args.backup_confirmed or os.getenv("CHRONOMIND_APPROVED_MIGRATION") != "1"
    ):
        parser.error("Apply requires --backup-confirmed and CHRONOMIND_APPROVED_MIGRATION=1")
    if not args.uid.strip():
        parser.error("--uid cannot be blank")

    docs = list(get_db().collection("users").document(args.uid).collection("tasks").stream())
    converted, invalid = [], 0
    for doc in docs:
        try:
            converted.append(convert_legacy_task(args.uid, doc.id, doc.to_dict() or {}, args.timezone))
        except (TypeError, KeyError, ValueError, OverflowError):
            invalid += 1
    print(f"Source documents: {len(docs)}; convertible: {len(converted)}; invalid/quarantined: {invalid}")

    if args.reconcile:
        from v2.models import Task, LegacyTaskArchive
        with Session(engine()) as db:
            pg_tasks = {
                t.legacy_id: t for t in db.scalars(
                    select(Task).where(Task.owner_uid == args.uid, Task.legacy_id.is_not(None))
                ).all()
            }
            archives = {
                a.legacy_id: a.source_hash for a in db.scalars(
                    select(LegacyTaskArchive).where(LegacyTaskArchive.owner_uid == args.uid)
                ).all()
            }
        reconciled = 0
        missing = []
        hash_mismatches = []
        for item in converted:
            if item.legacy_id not in pg_tasks:
                missing.append(item.legacy_id)
            elif archives.get(item.legacy_id) != item.source_hash:
                hash_mismatches.append(item.legacy_id)
            else:
                reconciled += 1
        print("--- MIGRATION RECONCILIATION REPORT ---")
        print(f"Verified matching records: {reconciled} / {len(converted)}")
        print(f"Unimported / missing in PostgreSQL: {len(missing)}")
        print(f"Hash checksum mismatches: {len(hash_mismatches)}")
        if not missing and not hash_mismatches and not invalid:
            print("RECONCILIATION RESULT: PASS (100% integrity verified)")
            return 0
        else:
            print("RECONCILIATION RESULT: DISCREPANCY DETECTED")
            return 1

    if invalid:
        print("STOP: malformed records require a private manual review before applying.")
        return 2
    if not args.apply:
        print("Dry run only: zero PostgreSQL writes; zero Firestore writes.")
        return 0

    counts = Counter()
    with Session(engine()) as db:
        with db.begin():
            db.scalar(select(User).where(User.uid == args.uid).with_for_update())
            for item in converted:
                result = import_converted(db, item)
                counts[result] += 1
    print(f"Applied PostgreSQL backfill (Firestore unchanged): {dict(counts)}")
    print("Perform independent source/target reconciliation (--reconcile) and browser QA before cutover.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
