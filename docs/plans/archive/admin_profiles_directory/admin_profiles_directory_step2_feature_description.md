# Admin Profile Directory – Step 2 Feature Description

## Problem
Administrators lack a consolidated view of every user profile on their instance, making it tedious to review account details, confirm contact emails, or confirm sharing scopes when mediating requests.

## User Stories
- As an administrator, I want to list every profile regardless of sync scope so I can verify who is active in the community.
- As an administrator, I want to filter or scan by username/contact email to answer support questions quickly.
- As an administrator, I want each entry to link to deeper context (request history, invite source) so I can take follow-up actions without leaving the directory.

## Core Requirements
- Add an admin-only route (e.g., `/admin/profiles`) listing all users with key fields: username, display label, contact email, created date, sync scope.
- Support basic search/filter inputs (username substring, contact email substring) processed server-side.
- Each row links to existing admin utilities (e.g., request feed filtered by user, invite history, or user detail view if available); if those pages don’t exist yet, include placeholders for future wiring.
- Respect pagination for large instances (default 25–50 rows with controls).
- Enforce admin permission checks and reuse existing layout patterns (admin shell, tables, chips).

## User Flow
1. Admin visits `/admin/profiles` from the admin navigation.
2. Page loads with a paginated table of users sorted by most recent activity/creation.
3. Admin enters a username/email fragment and submits the form to filter results.
4. Admin clicks on a row action to view related data (requests, invites, sessions) or copy the contact info.

## Success Criteria
- Admins can fetch the directory without API/CLI access; permission checks prevent non-admin access (403).
- Directory renders within 500 ms for 1k users and supports pagination/search without client-side JS.
- At least one link/action per row provides a path to deeper context (existing page or clearly labeled placeholder).
- Documentation (admin guide or changelog) describes how to reach and use the directory.
