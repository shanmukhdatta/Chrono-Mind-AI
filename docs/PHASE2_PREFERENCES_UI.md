# Planning preferences page — separate frontend PR

Route: `/preferences` in the existing signed-in application.

Supports view, reload and update for timezone, working hours, daily limit and breaks using the Phase 2 PostgreSQL API. Includes client-side validation tests and backend validation. Demo users are shown a truthful explanation rather than fake persistence.

This PR is stacked after the Goals UI PR. Real PostgreSQL API and authenticated browser verification are required for acceptance; full automatic scheduling enforcement is in a later phase.
