## Stage 1 – Surface session role metadata
- **Goal**: Provide templates and client code with a normalized role/access label for the signed-in user.
- **Dependencies**: None (uses existing `User` + `UserSession` data).
- **Changes**: Add a utility in `app/routes/ui.py` to derive role categories (`admin`, `member`, `pending`) from `User` and session state; include the resulting label (and optional styling hint) in the context returned by the home and pending dashboards.
- **Testing**: REPL or temporary unit-style check is optional; manual confirmation via debugger/logs during local run.
- **Risks**: Forgetting the half-authenticated path or mislabeling admins who are mid-verification (should still appear as admin if allowed).

## Stage 2 – Render role indicator in shared navigation
- **Goal**: Display the current role prominently in the header for all logged-in views without crowding the UI.
- **Dependencies**: Stage 1.
- **Changes**: Update `templates/base.html` (or nav blocks) to render a badge/label with the session role before the sign-out control; adjust `requests/index.html` and `requests/pending.html` nav blocks to include the new indicator alongside “Sign out.”
- **Testing**: Manual smoke check by logging in as admin, standard member, and half-auth user to verify the label updates and layout stays intact on desktop/mobile.
- **Risks**: Layout regressions in the narrow header or forgetting to hide the indicator on logged-out pages.

## Stage 3 – Refresh flows after state changes
- **Goal**: Ensure the indicator reflects role changes without a full page refresh.
- **Dependencies**: Stage 1.
- **Changes**: After successful verification (existing flow returns redirect), rely on server-rendered navigation. Confirm any JS-driven refreshes (e.g., HTMX) include the role label when re-rendering cards; if necessary, expose the role via `data-` attributes in `request-feed.js` for future use.
- **Testing**: Manual verification by completing verification flow and confirming the badge switches from “Pending verification” to “Member/Admin” on redirect.
- **Risks**: Missing contexts such as partial templates that assume the indicator exists leading to undefined references.
