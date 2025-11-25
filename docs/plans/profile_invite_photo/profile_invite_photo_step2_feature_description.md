# Profile Invite Photo Integration — Step 2 Feature Description

## Problem
Invite personalization allows uploading a welcome photo, but after the invited user joins, their profile still shows the default avatar. We’re missing a chance to highlight the inviter-provided image.

## User Stories
- As a new member, I want my profile to feel personal right away when my inviter uploaded a photo for me.
- As an inviter, I want the photo I prepared to appear on the invitee’s profile without additional steps.
- As a maintainer, I want a straightforward fallback so profiles without photos keep the existing default.

## Core Requirements
- When an invite includes a photo, link that asset to the created user during onboarding.
- Display the photo on the user’s profile page if present; fall back to the initials avatar otherwise.
- Ensure the photo respects existing dark/light theme styling and responsive layout.
- Leave room for future user-initiated avatar overrides (don’t block manual uploads later).

## User Flow
1. Inviter creates an invite with an uploaded photo.
2. Invitee registers; backend associates the invite photo with the new user record.
3. Visiting the user’s profile shows the photo as their avatar; default avatar appears if none exists.

## Success Criteria
- Invite photos automatically appear on the corresponding user profile after signup.
- Profiles without invite photos remain unchanged.
- Manual smoke test confirms the avatar looks correct in light/dark modes and responsive breakpoints.
