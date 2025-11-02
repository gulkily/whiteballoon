## Stage 1 – Surface completion permission in data layer
- **Goal**: Provide the frontend with an explicit `can_complete` flag per request.
- **Dependencies**: None.
- **Changes**: Extend `RequestResponse` model/serializer to include `created_by_user_id`; calculate `can_complete` in UI route serialization using current user + admin flag; ensure HTMX/JSON responses expose the flag without leaking extra PII.
- **Testing**: Unit-style check in a lightweight service or serializer test (if feasible) to confirm the flag values; otherwise manual inspection via temporary logging or shell.
- **Risks**: Forgetting half-authenticated sessions or admins when computing the flag; leaking unnecessary user data.

## Stage 2 – Update server-rendered templates
- **Goal**: Hide the “Mark completed” button unless `can_complete` is true.
- **Dependencies**: Stage 1.
- **Changes**: Adjust `templates/requests/partials/item.html` (and pending view if applicable) to branch on the new flag; ensure fallback spans/messages remain unchanged for completed requests.
- **Testing**: Manual smoke test by signing in as owner vs. non-owner; confirm admins still see the button.
- **Risks**: Missing a template path (e.g., pending list) and leaving old behavior in place.

## Stage 3 – Align dynamic updates
- **Goal**: Ensure the JavaScript-rendered list honors the same visibility rule.
- **Dependencies**: Stage 1.
- **Changes**: Update `static/js/request-feed.js` rendering to read `can_complete`; avoid emitting the form for users who cannot complete requests.
- **Testing**: Manual: trigger HTMX refresh (e.g., create request, switch users) and verify button behavior; optionally add a minimal frontend unit test if tooling exists.
- **Risks**: Cached markup reintroducing the button; missing partials used by HTMX responses.

## Stage 4 – Verification & cleanup
- **Goal**: Confirm end-to-end behavior and document results.
- **Dependencies**: Stages 1–3.
- **Changes**: Manual regression pass covering owner, non-owner, admin, and half-auth views; update implementation summary with findings.
- **Testing**: Manual only (UI walkthrough + ensure API still returns 403 when forcing POST as non-owner).
- **Risks**: Overlooking pending request edge cases; insufficient manual coverage leading to regressions.
