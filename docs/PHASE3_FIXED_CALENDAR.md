# PostgreSQL fixed-events API and unified calendar window

Authenticated routes:
- `GET /api/v2/fixed-events`
- `POST /api/v2/fixed-events`
- `PUT /api/v2/fixed-events/{event_id}`
- `DELETE /api/v2/fixed-events/{event_id}`
- `GET /api/v2/calendar?starts_at=<offset-aware>&ends_at=<offset-aware>`

All access is filtered by verified owner_uid. Creates and edits serialize on the PostgreSQL user's row (SELECT FOR UPDATE) before checking for overlaps with fixed events and schedule blocks. The range endpoint returns separate fixed and scheduled task blocks. This is not yet a new calendar frontend or a complete Firestore cutover.

Production PostgreSQL race tests, live Firebase identity tests and user-permission tests remain required. Do not claim atomic safety when accessing tables outside this write protocol.
