# Auth Flow Experience – Step 3: Development Plan

1. **Stage 1 – Half-auth page messaging cleanup**
   - **Goal**: Gate self-auth UI copy so pending users only see viable instructions; prep template hooks for polling.
   - **Dependencies**: Existing `templates/auth/login_pending.html`, `WB_FEATURE_SELF_AUTH` flag, shared styles from Step 2 inventory.
   - **Changes**: Add conditional blocks that hide the self-auth banner/form unless the flag is true; introduce semantic containers/data attributes so later stages can target status + message slots without duplicating markup.
   - **Verification**: Toggle feature flag locally, load pending page, confirm the self-auth copy appears/disappears accordingly and peer-auth guidance remains.
   - **Risks**: Forgetting translation/localization strings; regressions to approved self-auth flow.

2. **Stage 2 – Pending page auto-refresh + safe redirect**
   - **Goal**: Keep half-auth users updated and redirect them to a GET-safe destination once approved/denied.
   - **Dependencies**: Stage 1 template hooks, `app/routes/ui/__init__.py` session helpers, existing session status data (no new tables).
   - **Changes**: Add a lightweight status endpoint (e.g., `GET /auth/status`) returning session state; enhance pending template with JS polling (≤30s interval) to fetch status and redirect to `/` when fully authenticated; ensure server-side login completion paths redirect to `/` rather than re-rendering POST pages.
   - **Verification**: Walk through login → pending flow, approve the session via admin tools, observe automatic redirect and denial messaging without manual reloads; inspect network panel to confirm GET redirects only.
   - **Risks**: Polling too aggressively; redirect loops if session expires mid-request.

3. **Stage 3 – Half-auth notification for logged-in user**
   - **Goal**: Surface persistent in-app notification for any active session stuck in half-auth.
   - **Dependencies**: Stage 2 status endpoint, `templates/partials/account_nav.html`, existing badge styles.
   - **Changes**: Extend account nav context with structured notification data; render a dismissible note/badge tied to half-auth state; optionally reuse polling response to dismiss once status flips. No DB changes.
   - **Verification**: Log in with a half-auth session, confirm notification appears on all pages using the nav partial; approve session and ensure notification disappears without reload or on next poll.
   - **Risks**: Overlapping with admin badges; accessibility regressions if notification is only iconography.

4. **Stage 4 – Reviewer notifications for new pending requests**
   - **Goal**: Alert logged-in reviewers (admins/peer-auth roles) when new half-auth sessions need attention.
   - **Dependencies**: Peer-auth role checks, Stage 2 status endpoint or queue API, existing nav/header alert patterns.
   - **Changes**: Introduce a minimal notification feed (polling or SSE) that exposes “pending request count + latest requester name/timestamp”; update nav/menu to render a badge or toast linking to `/peer-auth`; ensure data only flows to authorized reviewers.
   - **Verification**: With two browsers, submit a login request while logged in as reviewer; confirm notification appears within 30s and link opens queue.
   - **Risks**: Over-notifying on already-open queue tabs; leaking requester names to unauthorized sessions.

5. **Stage 5 – Peer-auth queue auto-update**
   - **Goal**: Keep `/peer-auth` listings fresh without manual reloads.
   - **Dependencies**: Stage 4 notification plumbing (polling channel), existing queue template (`templates/peer_auth/index.html`) and list partials, queue JSON serialization helpers.
   - **Changes**: Add a JSON endpoint (or reuse status feed) returning queue entries with timestamps; enhance the queue page with JS that refreshes list rows, preserves filters/sort, and removes resolved sessions; ensure canonical list partial structure is reused (innerHTML swap) to avoid forking styles.
   - **Verification**: Open queue page, trigger new login + approval/denial cycles, confirm rows appear/disappear within polling window and reviewer filters remain intact.
   - **Risks**: DOM flicker if entire list rerenders; eventual consistency issues if approvals propagate slower than polling cadence.
