# Peer Authentication Queue · Step 3 Development Plan

## Stage 1 – Model peer-auth session listings
- **Goal**: Extract pending/half-auth sessions plus requester metadata for reviewer-only consumption.
- **Dependencies**: None.
- **Changes**: Add `peer_auth_service.py` with queries that join `AuthenticationRequest`, `UserSession`, and `User` to surface username, created_at, device/ip context, and current 6-digit code; include helpers for filtering (pending only) and pagination capped at ~25 rows. Add permission check utilities so only admins/whitelisted reviewers can call the listing function.
- **Verification**: Run the new service in a shell (e.g., `python -m app.tools.peer_auth debug-list`) to confirm it returns pending sessions with codes for seeded data.
- **Risks**: Accidentally exposing codes to unprivileged users—unit test the permission guard and keep helpers internal to reviewer routes.

## Stage 2 – Build reviewer inbox UI
- **Goal**: Create a dedicated reviewer-only inbox page that lists pending peer-auth sessions.
- **Dependencies**: Stage 1 data helpers.
- **Changes**: Add `app/routes/ui/peer_auth.py` with GET `/peer-auth` requiring logged-in reviewer/admin; register router in `app/routes/ui/__init__.py`. Create `templates/peer_auth/index.html` (and optional `static/css/peer_auth.css`) with a simple list/table showing requester, age, and status. Respect Step 2’s direction by not reusing the request queue components; keep markup self-contained and scoped styles under a new wrapper class.
- **Verification**: Launch dev server, visit `/peer-auth` as admin with fake pending sessions, ensure the list renders and hides for standard members.
- **Risks**: Routing conflicts or missing template context—log page access and add feature flag to hide link while developing if needed.

## Stage 3 – Detail drawer + approval form
- **Goal**: Let reviewers open a session, view the 6-digit code, and submit approve/deny decisions with notes.
- **Dependencies**: Stage 2 page scaffold.
- **Changes**: Add drawer/modal partial that loads via HTMX/alpine (or inline dynamic block) showing requester info, 6-digit code, attestation textarea, and approve/deny buttons. Implement POST endpoint(s) under `/peer-auth/{auth_request_id}` that call `auth_service.approve_auth_request` for approvals and a new helper to mark a request denied + expire its linked `UserSession`. Enforce that only current pending requests can be changed and record reviewer IDs + note text in memory for Stage 4 forwarders.
- **Verification**: Manually approve + deny sample requests and ensure the UI reflects new status plus session upgrade/expiration (e.g., pending entry disappears after refresh).
- **Risks**: Race conditions approving already-processed requests—detect stale status and return graceful errors.

## Stage 4 – Append-only SQLite ledger writer
- **Goal**: Persist every approval/denial to a dedicated SQLite database for auditing.
- **Dependencies**: Stage 3 decision handlers emit structured decision payloads.
- **Changes**: Create `app/services/peer_auth_ledger.py` that manages the SQLite file (e.g., `storage/peer_auth_ledger.db`), auto-creates tables (`decisions` table with reviewer_id, requester_id, session_id, auth_request_id, decision, note, timestamp, checksum seed). Hook Stage 3 endpoints to write rows via this service inside a try/except block; include checksum/hash (e.g., SHA256 of row contents) per entry to detect tampering.
- **Verification**: Trigger approvals/denials and inspect the SQLite file via `sqlite3 storage/peer_auth_ledger.db '.schema'` and `.tables` to confirm rows append with expected metadata.
- **Risks**: File permission issues or concurrent writes—use `sqlite3` in WAL/offline mode and wrap writes with locks to avoid corruption.

## Stage 5 – Ledger download + checksum surface
- **Goal**: Allow admins/auditors to fetch the ledger + checksum via the UI.
- **Dependencies**: Stage 4 ledger file exists and updates reliably.
- **Changes**: Extend admin exports route (e.g., add section on `/admin` or `/admin/exports`) with a download button linking to a new endpoint that streams the SQLite file plus a small text endpoint returning the latest checksum. Document the ledger location and include warnings about sensitive data. Optionally expose CLI command for checksum verification.
- **Verification**: Download the ledger through the browser and hash it locally (e.g., `shasum -a 256`) to confirm it matches the server-provided checksum.
- **Risks**: Large files or blocking IO; mitigate by using `StreamingResponse` and verifying headers to avoid caching stale snapshots.

## Stage 6 – End-to-end QA + instrumentation
- **Goal**: Validate the complete reviewer workflow and capture manual verification evidence.
- **Dependencies**: Stages 1–5 complete.
- **Changes**: Walk through the flow: create half-auth session, approve via inbox, confirm awaiting user session becomes fully authenticated, ensure denial path expires session. Update Step 4 implementation summary with observed behavior and add minimal logging/metrics (e.g., count of approvals) if missing.
- **Verification**: Document QA checklist results, including screenshots or notes for inbox view, ledger entry, and download checksum.
- **Risks**: Missed edge cases (expired auth requests still visible); add cron/service to purge aged entries if queue grows unexpectedly.
