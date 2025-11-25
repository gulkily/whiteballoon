## Problem
Admins currently generate invite codes through backend tooling, while new visitors who lack a token see a terse message with no clear next step. This creates friction for administrators onboarding helpers and leaves prospective members unsure how to request access.

## User stories
- As an administrator, I want a simple invite management UI so that I can create new invite codes without touching the command line.
- As a visitor without an invite, I want a friendly explanation and guidance so that I know how to request or redeem an invite.
- As a logged-in member, I want to see whether I have spare invite codes to share so that I can help grow the community when permitted.

## Core requirements
- Provide an authenticated UI surface (admin-only) to generate new invite codes and copy them easily.
- Improve the “no invite code” messaging with clear next steps or contact guidance without revealing sensitive admin details.
- Reflect invite generation results back to the user (success, error, remaining quota if applicable).
- Ensure non-admins and logged-out users cannot access invite management features.

## User flow
1. Admin signs in and navigates to the invite management screen from the profile or admin section.
2. Admin clicks “Generate invite,” sees confirmation, and can copy or share the new code.
3. Visitor without an invite lands on registration or invite-required page and sees friendly guidance on how to request access.
4. Admins and members continue normal workflow; invite messaging updates as codes are consumed.

## Success criteria
- Admins can create invite codes through the UI without errors (limit enforcement respected).
- The invite-required page provides a supportive explanation and suggested next steps instead of a dead end.
- Non-admin users cannot access the invite generation controls (attempts are rejected or hidden).
- Manual verification covers admin generation, visitor messaging, and basic access-control checks.
