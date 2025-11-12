## Problem
Administrators currently need shell access to configure peers, update hub credentials, or trigger sync operations. This blocks non-technical admins and slows down incident response when only the web UI is available.

## User Stories
- As an admin, I can review the configured peers (filesystem and hub) from the browser so I know which destinations are active.
- As an admin, I can update a peer’s token/public key or delete a peer without editing files manually.
- As an admin, I can trigger a push or pull from a peer in the UI and see confirmation that the job started.
- As an admin, I can view the most recent push/pull status (success, digest, timestamp) for each peer.

## Core Requirements
- New “Sync Control Center” page under the admin nav showing peer cards (name, type, destination path/URL, public key fingerprint, last sync metadata).
- Inline, server-rendered forms (no modals) to create/edit/remove peers (writing to `sync_peers.txt`). Validation should prevent conflicts and require tokens for hub peers.
- Buttons to trigger push/pull actions per peer; backend should run the existing CLI helpers asynchronously and surface a standard inline status/flash message using current assets only.
- Display recent sync results (at least the last push & pull timestamp/digest) using existing metadata files (`data/public_sync/manifest`, hub status endpoint, etc.).

## User Flow
1. Admin visits “Sync Control Center” from the top nav.
2. Page loads peer list + status summaries.
3. Admin clicks “Add peer” or selects “Edit” to reveal the inline form; upon save, the page reloads with the refreshed table.
4. Admin hits “Push now” or “Pull now” on a peer. UI shows “job queued” and, once finished, updates the status chip.

## Success Criteria
- Admins can manage peers and execute syncs entirely via UI (no shell commands required) for common tasks.
- Push/pull actions initiated from the UI trigger the same underlying logic as the CLI and provide visible success/failure feedback.
- Peer configuration changes are persisted to `sync_peers.txt` and reflected in subsequent CLI runs.
- The existing `/sync/public` dashboard remains available but now links to the Control Center for configuration tasks.
- No new frontend dependencies (e.g., HTMX/Alpine) are introduced; the page relies on current CSS/JS bundles.
