# PostgreSQL tasks frontend (V2)

The `/tasks-v2` authenticated page supports real create/read/edit/complete/reopen/archive of V2 tasks, goal linkage, effort estimates and deadlines. It uses the verified-Firebase-token API, optimistic `version` checks (HTTP 409) and explicit save messages only after successful requests. Deadline conversion uses browser-local datetime-local to ISO with UTC instant storage. Demo users cannot simulate persistence.

Task archiving is non-destructive. Marking complete does not auto-delete work blocks. Recurrence, dependencies, drag/drop scheduling and V1 Firestore cutover remain later phases. Verify browser flows, timezone and cross-user isolation with actual PostgreSQL in Antigravity.
