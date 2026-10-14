# V2 calendar screen

The authenticated route `/calendar-v2` displays the current day's PostgreSQL fixed commitments and approved task schedule blocks. Users can create, edit and delete fixed commitments, with conflict checks performed by the API. It deliberately coexists with the legacy Firestore `/calendar` view until controlled migration and final cutover.

All visible times use the device timezone. Preference timezone mismatch and daylight saving transitions require final acceptance testing; no implied full V1/V2 synchronization. Requires real PostgreSQL, Firebase credentials and browser QA. 
