# Invite Frontend UI — Step 3 Development Plan

1. **Stage 1: "Send Welcome" entry point**
   - Add a visible “Send Welcome” control for authenticated users (e.g., button in header/account menu or dashboard call-to-action).
   - Restrict access by redirecting unauthenticated users and hiding the control from those without invite permission if policy toggles exist.
   - Testing: Manual check for authenticated vs signed-out users.

2. **Stage 2: Invite page skeleton**
   - Create new route/template (e.g., `/invite/new`) that triggers invite creation on initial load (server-side or via fetch).
   - Render returned data (token, full link, QR) plus optional fields for invitee username/bio; include regeneration control.
   - Testing: Manual page load, ensure re-fetch works and errors show inline.

3. **Stage 3: Styling & accessibility polish**
   - Ensure layout responsive, copy buttons and QR display cleanly, optional fields labeled clearly.
   - Provide keyboard focus management and ARIA labels for interactive elements.
   - Testing: Manual keyboard navigation, mobile viewport.

4. **Stage 4: Documentation updates**
   - Update README/cheatsheet to mention the “Send Welcome” page, optional fields, and `SITE_URL` fallback.
   - Testing: Manual doc review.

5. **Stage 5: QA**
   - Run `pytest` (acknowledging current suite emptiness) and perform manual invite page walkthrough.
