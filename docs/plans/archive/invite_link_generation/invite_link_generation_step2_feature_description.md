# Invite Link Generation — Step 2 Feature Description

## Problem
Invite tokens are shown as raw strings; users must manually combine them with the site URL to share a registration link, increasing friction and error risk.

## User Stories
- As a user who just generated an invite, I want a one-click copyable link so I can share it immediately.
- As an admin, I want the link to use the correct base URL automatically so invitees land on the right server.
- As a maintainer, I want a safe fallback when the request origin isn’t available so local/dev setups still work.

## Core Requirements
- Extend the invite modal/template to display a fully qualified link (e.g., `https://example.com/register/XYZ`).
- Determine base URL from the incoming request (preferred) with fallback to a configured `SITE_URL` setting.
- Provide copy button / link text within the modal; keep QR functionality intact.
- Update CLI output to mirror the behavior (optional but low cost).
- Document the new behavior so admins know what base URL is used and how to override it.

## User Flow
1. User clicks “Generate invite” in the UI.
2. Modal shows the token, full invite link, and QR code.
3. User copies the link (or scans the QR) and shares it.
4. Invitee visits the link and lands on `/register` with token prefilled.

## Success Criteria
- Full invite link appears immediately after generation in the UI and uses the correct host/port.
- Registrants arriving via the link see the invite token pre-populated.
- CLI invite generation prints the full URL when possible.
- Documentation (README/cheatsheet) notes how the base URL is determined and how to override it.
