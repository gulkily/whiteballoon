## Stage 1 – Route + Template Skeleton
- Goal: Add `/admin/sync-control` route (admin-only) with base template + nav link.
- Changes: FastAPI route + permission guard, new Jinja template with empty layout sections; link from `/sync/public`.
- Verification: Access as admin loads page; non-admin receives 403.
- Risks: None (static page).

## Stage 2 – Peer Listing & Status Chips
- Goal: Render filesystem + hub peers with metadata (path/url, public key fingerprint, last sync times).
- Changes: Backend helper to read `sync_peers.txt`, call existing bundle metadata + hub status APIs; template loops over peers, shows status chips.
- Verification: Page lists current peers with expected info; missing metadata handled gracefully.
- Risks: Blocking calls if hub status is slow; mitigate with timeouts.

## Stage 3 – Add/Edit/Delete Peer Modals
- Goal: Allow admins to create, edit, and remove peers via forms.
- Changes: POST endpoints writing to `sync_peers.txt`, CSRF-protected forms (likely modals triggered via HTMX/alpine). Validation for duplicates, required fields.
- Verification: Create peer, edit token/public key, delete peer; changes reflected both in UI and file.
- Risks: Race conditions when multiple admins edit simultaneously (acceptable for MVP, but log warnings).

## Stage 4 – Trigger Push/Pull Actions
- Goal: UI buttons queue push/pull jobs using existing CLI functionality.
- Changes: Background tasks/celery-lite (FastAPI `BackgroundTasks`) invoking the same Python helpers used by CLI (export/import). UI shows toast on enqueue and refreshes status on completion.
- Verification: Trigger push/pull; watch logs + status chip update; ensure buttons disable while job in flight.
- Risks: Long-running job blocking request thread; need background task + status polling.

## Stage 5 – Activity Log & Notifications
- Goal: Display last N sync events (peer, action, timestamp, digest, result) and emit inline alerts when failures occur.
- Changes: Persist event log (e.g., JSON file or sqlite table) updated whenever push/pull completes; UI list with filters.
- Verification: Run push/pull; event log shows new entry; error case displays red badge.
- Risks: Need to ensure log writes are atomic; may require file lock or future DB table.

## Stage 6 – Documentation & Linking
- Goal: Update README/admin docs to describe the Control Center; add link from `/sync/public` and README quickstart.
- Changes: Append instructions, screenshots (optional), mention required permissions.
- Verification: Docs mention web-based workflow; nav link confirmed.
- Risks: None.
