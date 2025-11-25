1. Provide read-only profile route for arbitrary users  
   - Dependencies: User data already stored in `users` table; reuse existing `SessionDep`.  
   - Changes: add a new handler in `app/routes/ui.py` (e.g., `/people/{username}`) guarded by `require_session_user`; reuse or adapt the profile template to render another user’s details with safe fallbacks.  
   - Testing: manual request to `/people/<existing_username>` as admin and member; confirm 404 for unknown usernames.  
   - Risks: leaking sensitive data; mitigate by limiting displayed fields to username/contact email/created date already shown on own profile.

2. Update templates to link creator names  
   - Dependencies: Stage 1 route exists.  
   - Changes: wrap creator name in `templates/requests/partials/item.html` with an anchor to the new route, handling missing usernames gracefully.  
   - Testing: manual load of dashboard and pending view; ensure keyboard focus/ARIA remain intact.  
   - Risks: layout shift from link styling; adjust CSS if anchor inherits unexpected decoration.

3. Sync dynamic renderer and styling  
   - Dependencies: Stage 2 markup decisions.  
   - Changes: mirror the anchor element in `static/js/request-feed.js`; add CSS tweaks (e.g., underline on hover) to preserve current look without losing accessibility.  
   - Testing: submit a request to trigger live refresh; inspect in dev tools for consistent DOM.  
   - Risks: inconsistent markup between server and client; mitigate by copying exact structure.

4. Verification sweep  
   - Dependencies: prior stages.  
   - Changes: none (documentation/testing).  
   - Testing: manual — navigate as half-auth and full-auth users to ensure access; attempt to load missing user to verify error handling; note automated test gaps if tooling unavailable.  
   - Risks: forgetting to cover half-auth scenario; explicitly check both contexts.
