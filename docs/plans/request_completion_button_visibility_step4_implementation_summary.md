## Overview
- Added a shared `can_complete` permission flag so the UI and API know whether the current user may finish a request.
- Hid the “Mark completed” button in both server-rendered templates and dynamic JS when the viewer lacks permission, while keeping owners and admins unaffected.
- Centralized the completion authorization check to avoid drift between display logic and backend enforcement.

## Implementation notes
- `RequestResponse` now exposes `created_by_user_id` and `can_complete`; FastAPI routes populate the flag using the signed-in user context.
- UI serialization and templates consume the flag, allowing owners (even in read-only views) and admins to see the completion control.
- Request feed JavaScript renders the completion form only when `can_complete` is truly enabled (coerced from string/boolean values) and strips any lingering unauthorized forms after refresh, keeping dynamic updates aligned with the server.

## Testing
- Automated: unable to run (`python -m pytest` fails because `python` is not available in the environment).
- Manual: Pending (would verify by signing in as owner vs. non-owner vs. admin and exercising the completion flow).
