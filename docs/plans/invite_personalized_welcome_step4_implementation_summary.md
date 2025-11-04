## Stage 1 – Persist invite personalization data
- Added `InvitePersonalization` table keyed by invite token and extended `auth_service.create_invite_token` to accept structured personalization payloads, returning both token and stored record.
- Enhanced `/auth/invites` endpoint to require the new fields, validate inputs, build a friendly suggested bio, and return serialized personalization details alongside the invite metadata.

### Testing
- Manual: Pending — exercise the invite API via the "Send welcome" UI once front-end updates land; verify errors trigger when required fields are missing.

## Stage 2 – Refresh "Send welcome" form
- Rebuilt `templates/invite/new.html` with required personalization inputs (photo URL, gratitude, support, help examples, fun details) and richer preview panels.
- Added client-side validation, updated invite preview messaging, and extended CSS (`static/css/app.css`) to style the new form controls and profile preview.

### Testing
- Manual: Pending — run through the new form, ensure validation messages appear, and confirm preview updates after invite creation/regeneration.
