# V2 notifications page

Authenticated `/notifications-v2` displays actual PostgreSQL notifications with unread filtering, mark-read and mark-all-read actions. No demo success fallbacks. Generation is performed by a separate operator-enabled worker, not the frontend and not every web-worker lifespan.

No email, mobile push or SMS integration is claimed. Acceptance requires PostgreSQL and a manually triggered notifications worker, then reloading the UI to see the persistent message.
