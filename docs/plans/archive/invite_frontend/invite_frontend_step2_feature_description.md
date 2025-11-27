# Invite Frontend UI — Step 2 Feature Description

## Problem
Authenticated users currently lack an in-app workflow that generates an invite link/QR on demand; they must rely on CLI/API tools even though invite links are now available.

## User Stories
- As an authenticated user, I want a “Send Welcome” button/link that takes me to an invite page so I can generate an invite without the CLI.
- As the inviter, I want the page to immediately show the invite token, full link, and QR code, and let me optionally include a suggested username/bio for the invitee.
- As a user without invite privileges (if policy disallows), I shouldn’t see or be able to access the invite page.

## Core Requirements
- Add a “Send Welcome” control for authenticated users that navigates to a dedicated page (e.g., `/invite/new`).
- When the page loads, automatically generate or fetch a token using the existing `/auth/invites` endpoint, then render the token, shareable link, and QR code.
- Provide optional fields for suggested username/bio; capture them for display and future reuse (even if not persisted yet, show them in the page output).
- Allow regeneration/retry from the page; handle errors gracefully.
- Respect invite policy (hide link if invites disabled).
- Document the new flow and mention `SITE_URL` fallback for link generation.

## User Flow
1. User clicks “Send Welcome”.
2. Invite page loads, automatically fetching/generating a token.
3. Page displays link, token, QR, and optional fields; user can edit the fields and share.
4. User may regenerate token or simply copy the link/QR.

## Success Criteria
- Authenticated users can reach the invite page and immediately receive an invite token/link/QR.
- Optional username/bio fields are present and reflected in the share UI.
- Users without invite permission are denied/redirected.
- Documentation describes the new page and base URL logic.
