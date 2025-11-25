# Profile Comments – Step 2 Feature Description

## Problem
Profiles (including imported Signal personas) lack visible comment history, leaving operators without context on a member’s past outreach and limiting moderation.

## User stories
- As an admin reviewing a member, I want to see their latest public/private comments directly on the profile so I can quickly assess activity.
- As an admin, I want a paginated “All comments” view for a profile so I can audit older threads without hunting through individual requests.
- As a Signal-import operator, I want chat personas to surface their associated comments the same way native profiles do, so I can keep trust reviews consistent.

## Core requirements
1. Inline profile section that renders the N most recent request comments (configurable constant) with timestamps, request links, and scope badges.
2. Link/button from the profile to open a dedicated comments listing route (e.g., `/people/<username>/comments`) with pagination/filter support.
3. Dedicated listing page shows all comments (native + Signal) chronologically with request references and scope badges; access limited to admins (same as base profiles).
4. Both inline snippet and full listing reuse existing permissions: respect sync scope and hide comments the current viewer cannot access.
5. Progressive enhancement only—server-rendered HTML first; optional JS can layer enhancements later but isn’t required for launch.

## User flow
1. Admin opens a profile (native or Signal persona).
2. Inline “Recent comments” block shows the latest N comments with “View all” link.
3. Admin clicks “View all comments” → navigates to `/people/<id>/comments` (or similar) where full list paginates.
4. Admin scans comments, optionally filters by scope if future enhancements arrive, and returns to profile.

## Success criteria
- Recent comments block loads ≤ N entries without noticeable slowdown on profile render.
- Comments index page exposes pagination with consistent styling and shows all comments for the target identity.
- Permissions: non-admin visitors cannot see restricted comments beyond current behavior.
- Documentation updated (profile feature summary, Step 4 log) describing the new inline + listing experience.
