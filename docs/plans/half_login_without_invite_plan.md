## Feature Description

Enable a feature-flagged mode where users can initiate a "half-login" (pending session + verification flow) without needing an invite token. This reduces onboarding friction for open pilots while preserving admin approval and verification safeguards.

### User Stories
- As a new user without an invite, I can request access and receive a verification code to complete login when approved.
- As an admin, I can control whether invite-less half-login is permitted and review pending requests.
- As an operator, I can toggle the feature via environment configuration without code changes.

### Core Requirements
- Config flag: `ALLOW_HALF_LOGIN_WITHOUT_INVITE` (default: false).
- When enabled:
  - Registration page clearly explains invite-less flow and routes users to login instead of hard erroring.
  - Login flow allows creating an `AuthenticationRequest` for unknown usernames (auto-create a user record with `is_admin=false`).
  - Created users are not fully authenticated until verification is completed and (optionally) admin approves.
- When disabled (current behavior):
  - Registration requires invite token (except first admin).
  - Login requires existing user.

### Success Criteria
- Flag off: behavior unchanged.
- Flag on: unknown username login yields pending session and verification code; no database errors; UI reflects pending status and guidance.

## Development Plan

1) Configuration
- Add `ALLOW_HALF_LOGIN_WITHOUT_INVITE: bool` to `app/config.py` with env var support.

2) Service changes
- Add `create_user_if_allowed(session, username, contact_email)`:
  - If user exists → return it.
  - If not and flag enabled → create new non-admin user without invite.
  - Else → raise 404 equivalent for login path.
- Update `auth_service.create_auth_request` call sites to accept user created via above helper when login attempts use unknown username and flag is enabled.

3) UI changes
- Registration form:
  - On "Invite token required" condition, render friendly page (done) with copy that references the feature, when enabled, to try login instead.
- Login form:
  - If unknown username and flag enabled → create user and proceed to pending verification screen.
  - If disabled → current error message preserved.

4) Admin and visibility
- No new admin UI needed initially; rely on existing session approval flow.
- Optional: add a banner on pending page indicating "Invite-less access is enabled by the operator".

5) Tests
- Unit: config flag parsing, `create_user_if_allowed` behavior.
- Integration: login unknown user with flag on → pending screen; flag off → error.

6) Rollout
- Ship behind flag defaulting to false.
- Document security implications in README.

## Risks and Mitigations
- Spam accounts: require verification code, optional rate limiting, and keep default off.
- Confusion between register vs login: enhance copy to route users appropriately when the flag is on.

## Acceptance Checklist
- [ ] Flag off preserves existing behavior for register and login.
- [ ] Flag on allows unknown user login to create pending session and user.
- [ ] UI copy updated on register and pending pages to explain the flow.
- [ ] Tests added and passing.

