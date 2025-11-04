## Stage 1 – Persist invite personalization data
- Added `InvitePersonalization` table keyed by invite token and extended `auth_service.create_invite_token` to accept structured personalization payloads, returning both token and stored record.
- Enhanced `/auth/invites` endpoint to require the new fields, validate inputs, build a friendly suggested bio, and return serialized personalization details alongside the invite metadata.

### Testing
- Manual: Pending — exercise the invite API via the "Send welcome" UI once front-end updates land; verify errors trigger when required fields are missing.
