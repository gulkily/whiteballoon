# User Attributes Schema — Step 2 Feature Description

## Problem
We cannot record relationships like "who invited this user" without altering the `users` table. We need an extensible mechanism to attach structured attributes to users without repeated schema migrations.

## User Stories
- As a developer, I want to persist inviter information for each user so that I can surface who invited whom and build invite analytics.
- As a developer, I want to add new user metadata (e.g., profile flags, onboarding milestones) without database migrations so that delivery stays agile.
- As a developer, I want consistent APIs for reading and updating user attributes so that business logic can rely on a single pattern.

## Core Requirements
- Create a `user_attributes` table capturing `user_id`, `key`, `value`, and timestamps, keyed uniquely per (`user_id`, `key`).
- Add SQLModel definitions and helpers to read, write, and delete attribute entries in an ergonomic manner.
- Migrate inviter data going forward by storing the inviting user’s ID or token in the attributes table (e.g., key `invited_by_user_id`).
- Ensure attribute access is performant via indexes and eager loading where appropriate.
- Guard access so only authenticated contexts with proper authorization can mutate attributes.

## User Flow
1. When a user action (e.g., invite acceptance) occurs, application code writes the relevant attribute to `user_attributes`.
2. Subsequent reads (profile, analytics) retrieve attributes via helper utilities and return structured data.
3. Developers add new attribute keys by convention without schema changes.

## Success Criteria
- New `user_attributes` table exists with uniqueness constraint on (`user_id`, `key`) and supporting indexes.
- Application code can set and retrieve inviter data through helper functions in local testing.
- Adding a new attribute key requires no database migration—only application logic changes.
- Performance stays acceptable (single additional query or join) when loading attributes for a user profile.
