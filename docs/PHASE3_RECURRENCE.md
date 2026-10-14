# V2 recurrence engine

Authentic user-owned recurrence series support daily or specified weekly weekdays, explicit start/end dates, optional local due time with IANA timezone, pause/resume, one-off skip exceptions and bounded idempotent materialization into persistent V2 tasks.

API: GET/POST `/api/v2/recurrence`, POST `/{id}/materialize?days=30` (max 90), POST `/{id}/pause`, `/{id}/resume`, `/{id}/skip` with `{"occurrence_date":"YYYY-MM-DD"}`.

Materialized occurrences are logical tasks; the scheduling engine proposes their work sessions separately. Materialization is explicitly invoked; **a recurring job to extend horizons has not yet been deployed**. Repeated calls deduplicate by (series_id, date). Skips archive unscheduled pending occurrences, but refuse to discard completed or already scheduled work. Pausing never deletes tasks. More advanced monthly/nth-weekday patterns and edits to historical series remain future features.

Live PostgreSQL, concurrent materialization and DST ambiguity tests need additional acceptance verification before enabling production schedules.
