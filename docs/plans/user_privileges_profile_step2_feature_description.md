# User Privileges Profile — Step 2 Feature Description

## Problem
Signed-in users lack a clear way to confirm which account is active and what privileges (including admin and half-auth status) they hold, leading to confusion and avoidable support requests.

## User Stories
- As a signed-in user, I want my username in the header to link to my profile so that I can quickly confirm who I am using the app as.
- As a signed-in user, I want a subtle indicator near my username that shows whether I am an admin and whether I am half-authenticated so that I can confirm my status at a glance.
- As a signed-in user, I want a dedicated profile view that spells out my identity details and privilege assignments so that I understand my access level.
- As a signed-in user, I want an easy handoff from the profile to existing account management areas so that I can adjust my information as needed.

## Core Requirements
- Render the header username as a link for authenticated users, routing to a protected profile page; hide the affordance from anonymous visitors.
- Display a compact status badge/indicator adjacent to the username that reflects admin role and half-authenticated state without dominating the header layout.
- Build a profile page that presents identity information (name, email, organization) and a structured list of privileges with plain-language explanations, all sourced from existing models.
- Apply current authorization rules so the profile page and indicator never expose data to unsigned users; unauthorized requests redirect to sign-in.
- Provide a clear link from the profile page to existing settings or account management interfaces when available.

## User Flow
1. User signs in and sees their username rendered as a header link with adjacent status indicator.
2. User clicks the username to open the profile page.
3. Profile page loads identity details and privilege descriptions using existing data sources.
4. User reviews privileges and, if needed, follows the link to manage settings.

## Success Criteria
- Username link appears only for authenticated users and reliably routes to the profile page.
- Status indicator displays the correct admin/half-auth state in a compact format across supported viewports.
- Profile page displays accurate identity and privilege information for at least three representative roles during testing.
- Unauthorized access attempts redirect to sign-in.
- Usability checks confirm that 90% of tested users can describe their privileges within 10 seconds of landing on the profile page.
