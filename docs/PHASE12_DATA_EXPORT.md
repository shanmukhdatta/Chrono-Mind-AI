# V2 PostgreSQL account data export

An authenticated `GET /api/v2/account/export` returns user-owned records from all application-managed V2 SQLAlchemy tables, with anti-cache headers and no client-provided owner UID. Includes goals, logical tasks, calendar sessions, preferences, proposals, recurrence, focus, consent, behavior events, deadline notifications and original Firestore task archive.

Limitations are explicit in every response. The old Firestore V1 account is separate and **not included**. LangGraph checkpoint internals are separate and **not included**. The export is bounded to 5,000 rows per table to protect API memory; oversized exports require an operator-assisted streaming export.

This is read-only. There is deliberately no "delete all V2 data" endpoint yet, because comprehensive deletion must first handle PostgreSQL application tables, LangGraph checkpoint tables, original Firestore data, and Firebase authentication/retention safely. Do not imply otherwise.

Manual acceptance: real Firebase ID token, PostgreSQL data, two unrelated users and an actual browser JSON download. Never log, email, or commit export files.
