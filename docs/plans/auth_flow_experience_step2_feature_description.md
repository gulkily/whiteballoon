# Auth Flow Experience – Step 2: Feature Description

## Problem
Users waiting for authentication or reviewing pending sessions receive stale pages, redundant warnings, and confusing redirects. Reviewers and logged-in members miss timely cues about half-auth status changes, leading to delays and duplicate support loops.

## User stories
- As a pending user, I want the half-auth page to refresh automatically so I see approvals instantly without manual reloads.
- As a person finishing authentication, I want to land on the proper dashboard instead of resubmitting forms so I can resume work immediately.
- As an already logged-in member who is still half-auth, I want a persistent notification so I know to finish verification.
- As a logged-in reviewer, I want a proactive notification when another user is waiting for approval so I can decide whether to grant access without camping on the queue page.
- As a reviewer watching the peer-auth queue, I want the queue view to auto-update so I never approve stale requests.
- As an admin controlling self-auth, I want disabled states hidden from users so we avoid confusing instructions.

## Core requirements
- Remove or hide the self-auth instructions/banner when the self-auth feature flag disables that pathway, while leaving peer-approval guidance intact.
- Add lightweight auto-refresh (polling or SSE) to the half-auth waiting page so approvals, denials, and new instructions appear without user input within a short window (<30s).
- After successful authentication (self, peer, or admin path), redirect users to a non-post/get-safe destination such as `/` or dashboard, never back to POST-only forms.
- Surface an in-app notification for logged-in half-auth sessions so they understand limited access until full verification completes, with dismiss rules tied to state changes.
- Trigger real-time or periodic notifications for logged-in reviewers when new half-auth requests arrive so they can take action even away from the queue view.
- Auto-update the peer-auth queue page so new pending sessions and status changes appear in place, preserving reviewer sort order and filters.

## Shared component inventory
- `templates/auth/login_pending.html` (half-auth waiting page) – reuse the existing template, extending it with conditional messaging and progressive enhancement hooks for polling.
- `templates/partials/account_nav.html` + header badge styles – reuse the half-auth indicator and extend it with notification messaging, avoiding duplicate status UI.
- `templates/peer_auth/index.html` and associated queue list partials – enhance the existing queue table/list with refresh hooks instead of creating a new view.
- `app/routes/ui/__init__.py` authentication handlers – ensure redirect targets and state transitions reuse the canonical session helpers already used for login/logout.

## User flow
1. Visitor submits username, receives half-auth session, and lands on the pending page that now polls for updates and only shows relevant instructions.
2. Peer reviewer or self-auth (if enabled) completes verification; backend marks the session fully authenticated.
3. Pending user’s page notices the status change, displays confirmation, and redirects them to the full dashboard without requiring another POST.
4. Logged-in users who remain half-auth see a persistent badge/notification in the account nav until approval completes.
5. Logged-in reviewers receive notifications (banner/toast/badge) when new pending requests arrive, with links to approve or dismiss.
6. Reviewers load `/peer-auth`, which now refreshes periodically to show the live queue and status transitions without manual reloads.

## Success criteria
- Half-auth page reflects approvals/denials within 30 seconds of a reviewer action in manual tests.
- Successful authentication redirects always land on `/` (or configured dashboard) without resubmitting form data (confirmed via browser devtools/network logs).
- When `WB_FEATURE_SELF_AUTH` is disabled, no “self-auth” messaging or controls appear in the pending/login UI.
- Half-auth sessions display the new notification, and it disappears immediately once the session becomes fully authenticated.
- Logged-in reviewers observe the new pending-request notification within 30 seconds of a half-auth request appearing, and can reach the queue directly from it.
- Reviewers watching the peer-auth queue observe new requests appearing and resolved sessions disappearing without page reload for at least a five-minute observation window.
