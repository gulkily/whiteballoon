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

## Stage 3 – Enhance registration welcome
- Updated `/register` handler to fetch invite personalization data and pass it to the template alongside existing suggested inputs.
- Expanded `templates/auth/register.html` to render the personalized welcome card (photo, gratitude, support, help list, fun details) while falling back to the legacy note when metadata is absent.

### Testing
- Manual: Pending — follow a generated invite link to confirm the welcome card appears with supplied data and that registration still works without personalization.

## Stage 4 – Verification snapshot
- Attempted to run automated tests (`pytest`), but the command is unavailable in this environment.
- Manual walkthrough deferred: need to generate an invite, validate the new required field flow, and complete registration using the invite link.

### Testing
- Automated: `pytest` (not run — command missing).
- Manual: Pending — requires live app session to exercise invite + registration journey.
