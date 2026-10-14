# V2 recurring task interface

Protected `/recurrence-v2` page connects to real V2 recurrence APIs. Supports daily and selected weekly days, explicit dates, optional due time and timezone, importance, materialize next 30 days, pause/resume and skip-date exceptions. No fake background materialization and no automatic deletion of completed task records.

Manual QA: real Firebase user and PostgreSQL, future date generation, repeat without duplicates, skip before/after materialization, incorrect IANA zone, daylight-saving transition, cross-user URL denial and browser refresh persistence. Monthly recurrence and edits to existing series are not yet implemented.
