## Problem
Members cannot easily confirm which account they are using. The header shows the role badge, but not the username or a path to view/edit their profile, making it hard to switch accounts or verify contact info.

## User stories
- As a signed-in member with multiple accounts, I want to see my current username so that I avoid posting under the wrong identity.
- As an administrator, I want quick access to my profile to verify my contact details and session info so that I can confirm I am using the correct admin account.
- As a half-authenticated user, I want to know which username is pending approval so that I can follow up with an admin if needed.

## Core requirements
- Display the active username alongside the role badge in the global header for all authenticated views.
- Add a profile entry point in the top navigation (icon + link) that routes to a dedicated profile page.
- Ensure the username indicator and profile link work for full, half-authenticated, and admin users without exposing sensitive data.
- Keep the logged-out experiences unchanged.

## User flow
1. User signs in; header renders with role label, username, and profile icon.
2. User clicks the profile icon/link.
3. Application serves a profile page showing basic account details and future settings placeholder.
4. User can navigate back or continue to other sections without losing context.

## Success criteria
- Authenticated users see their username next to the role badge on every page with the primary navigation.
- Clicking the profile icon routes to a profile view that clearly states the username and role status.
- Half-authenticated users also see the username and pending status; logged-out users never see profile controls.
- Manual verification covers role badge, username, and profile link across admin, member, and pending accounts.
