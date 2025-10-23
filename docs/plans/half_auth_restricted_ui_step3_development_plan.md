# Half-Authenticated Restricted UI – Development Plan

1. **Session State Audit & UX Sketch**
   - Dependencies: Feature description approved.
   - Changes: Confirm how `UserSession` and onboarding routes signal half-auth state; outline desired UI (read-only feed, code display, messaging, draft affordance).
   - Testing: Manual checklist of session states; verify existing flows (logged out, half, full).
   - Risks: Missing edge cases where session state inferred incorrectly; mitigate via exhaustive review of login/verify/logout paths.

2. **Pending Dashboard View**
   - Dependencies: Stage 1 UX outline.
   - Changes: Introduce pending template/partials for `/` when session is half-auth (includes verification code, instructions, read-only feed snapshot). Surface drafts UI stub (client-side indicator, disabled submit).
   - Testing: Browser smoke test ensuring logged-out/full sessions unaffected; verify pending page shows correct data.
   - Risks: Routing conflicts; mitigate by keeping logic contained in `/` handler.

3. **Draft Handling & Guardrails**
   - Dependencies: Stage 2 pending view.
   - Changes: Adjust request creation endpoints to block half-auth persistence (return 403 or stash client-side). Add JS/local storage helper so drafts survive page reload while pending.
   - Testing: Manual: attempt to submit request while pending (should stay local), refresh page (draft still available), post approval (draft can be submitted).
   - Risks: Losing drafts; mitigate with explicit storage and messaging.

4. **Spec & Docs Update**
   - Dependencies: UI changes complete.
   - Changes: Update `docs/spec.md`, README/guide if needed with the new state and UX; ensure plans reflect final behavior.
   - Testing: Doc review; `git grep` for outdated messaging.
   - Risks: Documentation drift; mitigate with final checklist.
