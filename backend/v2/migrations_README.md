# PostgreSQL V2 schema

The V2 endpoints use PostgreSQL separately from the legacy Firestore endpoints. No automatic table creation or migration occurs on server startup. Schema migrations are explicitly run through Alembic. Importing the app with no DATABASE_URL leaves legacy routes working; requests to /api/v2/* return a configuration error.

All tenant-owned tables have owner_uid and every query must be scoped to the verified Firebase ID token. All POST/PATCH bodies exclude owner_uid. Logical tasks are separate from time blocks. The initial schema reserves space for future planning and audit models that will be added through ordered migrations.

**Do not point DATABASE_URL at production before reviewing migrations and backing up source records.**
