## Problem
Signed-in users cannot see which role or access level they currently hold, leading to confusion about available actions (e.g., admin overrides vs. standard helpers).

## User stories
- As a regular member, I want to confirm I am signed in as a standard helper so that I understand why certain admin-only controls are hidden.
- As an administrator, I want to see that I am operating with admin privileges so that I can confidently perform elevated actions.
- As a half-authenticated user, I want to know that my access is limited until I finish verification so that I understand why the interface is read-only.

## Core requirements
- Surface the current session’s role/access level in the primary navigation or header without cluttering the UI.
- Distinguish between admin, full-authenticated member, and half-authenticated states using clear wording.
- Ensure the indicator updates immediately after authentication state changes (e.g., completing verification).
- Avoid exposing sensitive member data when rendering the indicator.

## User flow
1. User signs in or lands on the app and the session is resolved.
2. UI fetches or receives the current role/access status alongside existing session context.
3. Header or account section renders the role indicator appropriate to the user (admin, member, half-auth).
4. When the user’s session escalates (verification completed) or changes (logout/login), the indicator refreshes to reflect the new status.

## Success criteria
- Every logged-in view shows a visible role/access badge or label within one screen of the main navigation.
- Admin users see an explicit admin indicator; non-admins never see admin-specific messaging.
- Half-authenticated users see an indicator clarifying their limited access until verification completes.
- Manual verification: switching between user types updates the indicator without a hard refresh.
