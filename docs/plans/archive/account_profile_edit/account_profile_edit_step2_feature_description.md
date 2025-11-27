## Problem
Members cannot update their contact email or profile photo once registered, so they must ask admins for changes and can’t keep their info fresh on their own.

## User Stories
- As a member, I want to edit my contact email so I can receive replies at my current address.
- As a member, I want to upload or replace my profile photo to better represent myself in the community.
- As a member, I want validation feedback if I enter an invalid email or upload an unsupported image so I know how to fix it.
- As a member, I want the page to remind me of my current details so I can confirm what’s on file before saving changes.

## Core Requirements
- Add an authenticated settings route/page that loads the current user’s contact email and profile photo.
- Provide form controls to update the email (text input) and upload a new photo (file input) with basic server-side validation.
- Persist changes using existing `User` fields for email and the `profile_photo_url` attribute, storing new uploads via the established file storage pattern.
- Show clear success/error states after submission without exposing details to other users.
- Reuse existing authentication/session enforcement so only the logged-in user can edit their own details.

## User Flow
1. Member opens the “Account settings” page from their profile/navigation.
2. Server displays the current email and profile image with editable controls.
3. Member updates fields and submits the form.
4. Backend validates input, stores the new email/photo (upload -> URL -> attribute), and reloads the page with a success message.
5. If validation fails, the page re-renders with inline error messaging and preserves the entered values for correction.

## Success Criteria
- Authenticated members can reach the settings page and see their existing information prefilled.
- Valid updates persist to the database/attribute store and reflect immediately on reload (profile cards, invite map avatar, etc.).
- Invalid inputs surface errors without losing other form data, and no changes are written.
- Photo uploads accept standard image formats (jpg/png/webp) and reject oversized files per existing limits.
- Implementation stays within the current server-rendered stack (FastAPI + Jinja) without introducing new JS frameworks.
