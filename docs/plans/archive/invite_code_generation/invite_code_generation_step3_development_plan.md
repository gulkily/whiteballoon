## Stage 1 – Admin invite-management endpoint
- **Goal**: Provide a server-rendered route for admins to generate invite codes.
- **Dependencies**: Existing invite creation service; admin auth guard.
- **Changes**: Add a new route in `app/routes/ui.py` (e.g., `/admin/invites`) protected by `require_admin`. Within, handle GET to render existing invites and POST to create a new invite by calling `auth_service.create_invite_token`. Limit exposure of invite metadata to token, max uses, expiry, created timestamp.
- **Testing**: Manual toggle; optional unit around invite serialization.
- **Risks**: Accidentally exposing invite tokens to non-admins or leaking user data tied to invites.

## Stage 2 – UI for invite generation
- **Goal**: Present a simple admin UI for creating invites.
- **Dependencies**: Stage 1.
- **Changes**: Create `templates/admin/invites.html` with a form to generate a new invite (max uses, expiry). Use HTMX or standard post/redirect to reflect the new invite; display a list of recent invites with copy buttons.
- **Testing**: Manual verification via browser; ensure CSRF/safety is consistent with current forms.
- **Risks**: Form validation gaps; cluttered layout on mobile.

## Stage 3 – Friendly “no invite code” messaging
- **Goal**: Improve UX for visitors lacking invites.
- **Dependencies**: None (can be done in parallel).
- **Changes**: Update `templates/auth/invite_required.html` (and any inline message on registration) with more supportive copy, a prompt to contact admins, and a link to request an invite (e.g., mailto or support channel). Optionally add a small callout on `/register` explaining the process.
- **Testing**: Manual check that messaging appears and doesn’t leak admin emails.
- **Risks**: Over-promising contact paths, revealing private admin info.

## Stage 4 – Navigation entry point
- **Goal**: Ensure admins can reach invite management easily.
- **Dependencies**: Stage 2.
- **Changes**: Add an “Invites” link/icon in the authenticated nav (visible only to admins) pointing to the new route. Ensure the profile nav stays uncluttered.
- **Testing**: Manual admin session to confirm link visibility; non-admins should not see it.
- **Risks**: Link appearing for non-admins due to caching or context mix-ups.
