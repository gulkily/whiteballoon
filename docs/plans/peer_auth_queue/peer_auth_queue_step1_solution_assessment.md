# Peer Authentication Queue · Step 1 Solution Assessment

**Problem statement**: Admins need a verifiable way for logged-in members to approve half-authenticated sessions by confirming the user’s out-of-band 6-digit code, while writing every decision to an auditable ledger.

**Option A – Extend help-request queue + Signal Ledger timeline**
- Repurpose the existing help-request queue to store authentication requests (new type + statuses) so they appear in the current queue UI and inherit filtering, assignment, and pagination.
- Surface the awaiting user’s 6-digit code inside the existing request detail drawer for authenticated reviewers, and emit approval events to the Signal Ledger timeline (same template/skin) for transparency.
- Pros: Minimal new UI; reuses ORM models, queue routing, and ledger partials; quickest path to exposing the code to reviewers inside a flow they already trust.
- Cons: Overloads the help-request taxonomy with authentication-specific states; ledger events remain mixed with unrelated requests, so auditing auth approvals requires extra filtering; risk of accidental edits to request metadata impacting login flows.

**Option B – Dedicated peer-auth queue + append-only ledger tables (reusing shared UI partials)**
- Introduce dedicated `peer_auth_sessions` + `peer_auth_events` tables that track request lifecycle (pending, half-authenticated, approved) with an immutable approval ledger keyed to each session, then render them through new queue endpoints that reuse the existing card/list partials and Signal Ledger skin components.
- Display the 6-digit code inside the queue approval modal and require reviewers to attest (checkbox + note) before recording the event in the ledger, which would support export/filters without polluting help-request data.
- Pros: Clear separation of concerns, auditable append-only log purpose-built for authentication, easier to lock down permissions, and future-ready for additional verification methods (voice, TOTP) without touching help requests.
- Cons: Requires new DB objects + migrations, brand-new queue routes + templates, more verification plumbing (permission checks, pagination, API), and introduces parallel queue UX to maintain.

**Option C – Lightweight approval inbox + dedicated SQLite ledger**
- Capture half-auth sessions in a simple inbox (list + detail modal) backed by existing session store records; the awaiting user’s 6-digit code appears inside that modal for logged-in reviewers.
- Record approvals/denials into a separate append-only SQLite database that stores reviewer, timestamp, session metadata, and attestation text; expose downloads/export tooling for the ledger so auditors can inspect the file directly.
- Pros: Fastest to bootstrap (no new primary tables if we piggyback on session store), SQLite ledger is portable + queryable without touching core DB, avoids modifying the help-request ecosystem, and still gives us cryptographically verifiable audit history if we checksum the ledger file.
- Cons: Inbox UX still needs bespoke styling without shared queue components, SQLite ledger requires rotation/backups outside the main ORM, and live in-app filtering/reporting would need custom queries against the SQLite file.

**Recommendation**: Option C. The lightweight inbox paired with a dedicated SQLite ledger delivers the fastest path to peer approvals, isolates the audit log from the main database, and keeps the scope tight enough to ship quickly while still surfacing the 6-digit code to trusted reviewers. We accept the bespoke inbox styling because the portable ledger and minimal schema changes meet the admin goal without entangling help requests.
