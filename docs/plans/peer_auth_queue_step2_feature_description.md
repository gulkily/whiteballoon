# Peer Authentication Queue · Step 2 Feature Description

**Problem**: Half-authenticated users currently stall because no peer review workflow exists to confirm their 6-digit pairing code, so admins lack a transparent way to approve or audit these sessions.

**User stories**
- As an awaiting user, I want to know a logged-in peer can see my 6-digit code so we can verify it via a trusted channel and finish sign-in.
- As a logged-in reviewer, I want a queue of pending peer-auth sessions so I can inspect details, confirm the 6-digit code with the requester, and record my approval/denial.
- As an admin, I want every approval/denial captured in a ledger I can download so I can audit who verified which session and why.
- As an auditor, I want ledger entries to include reviewer identity, timestamps, and notes so I can trace any questionable access.

**Core requirements**
- Display a lightweight peer-auth inbox listing pending and half-authenticated sessions, ordered by age and limited to authorized reviewers.
- Provide a detail modal or drawer that shows the requester’s display info plus the current 6-digit code so reviewers can confirm it through an out-of-band channel before approving.
- Capture reviewer decisions (approve/deny + attestation note) and append them to a dedicated SQLite ledger file along with immutable metadata (timestamps, session identifiers, requestor/reviewer IDs).
- Offer admins a UI affordance to download/checksum the ledger file so any member with access can independently audit decisions.
- Reflect approval outcomes back into the authentication flow so an approved session upgrades to full authentication while denials expire the pending session.

**Shared component inventory**
- Requests queue list + detail drawer templates (`templates/requests/`) – not reused because peer-auth sessions expose different metadata (6-digit code, session state) and require reviewer-only visibility, so we will build a slim dedicated inbox layout.
- Signal Ledger metrics/timeline partials (`templates/requests/partials/signal_ledger_*.html`) – not reused since the ledger lives in a separate SQLite file; instead we expose downloadable artifacts rather than inline KPIs.
- Admin downloads or data-export endpoints (`app/routes/ui/admin.py` etc.) – will be extended to expose the SQLite ledger download link and checksum so auditors can self-serve without learning a new surface.

**User flow**
1. Awaiting user reaches the half-auth screen and is instructed to share their 6-digit code with a trusted member.
2. Logged-in reviewers visit the peer-auth inbox, see pending sessions, and open a request to view session metadata plus the 6-digit code.
3. Reviewer confirms the code with the requester over an external channel (call, chat) and records approve/deny plus an optional attestation note in the modal.
4. System stores the decision in the SQLite ledger, updates the session state (promote or expire), and reflects the outcome to both participants.
5. Admins or auditors can download the ledger file (and checksum) from the admin exports surface to verify activity whenever needed.

**Success criteria**
- ≥90% of half-authenticated sessions receive a peer decision within 10 minutes of appearing in the inbox during pilot.
- Every approval/denial produces an immutable ledger row containing reviewer ID, requester ID, session identifier, timestamp, and note.
- Admins can retrieve the ledger file and checksum through the UI without server access, and the file matches on repeated downloads.
- Awaiting users report (via support queue) that they were able to confirm the 6-digit code with a reviewer and complete login without staff intervention.
