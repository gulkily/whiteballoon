# Members list page — Step 2: Feature Description

## Problem
Members can only view their own profile; `/admin/profiles` is admin-only. We need a dedicated `/members` experience with a softer, member-friendly layout so people can browse the community while respecting existing privacy scopes.

## User stories
- As a fully authenticated member, I want a `/members` page with approachable cards so I can scan who’s active.
- As a member, I want simple filters (username/contact) so I can find someone even if I only know part of their handle or email.
- As a privacy-conscious member, I want my private scope honored except for people I invited, so I feel safe being listed.
- As an admin, I want the directory to reuse existing data sources and permissions so the view stays up to date without drift.

## Core requirements
- `/members` route available to fully authenticated sessions; deny half sessions and guests with the existing guard.
- Card-based layout (2–3 columns responsive) showing avatar placeholder, `@username`, join date, optional contact chip (only if viewer is admin or profile is public), and sharing scope badge.
- Filters for username + contact implemented with GET params; submit reloads the page; pagination uses the same `PAGE_SIZE` as admin directory but visually integrated into the member layout.
- Cards link to canonical profile detail: `/profile/<username>` for members viewing peers, `/admin/profiles/<id>` for admins (still accessible via new card link so they don’t lose admin context).
- Visibility logic: admins see all; members see users with `sync_scope == public` plus anyone they invited (via `INVITED_BY_USER_ID` attribute). Private profiles not invited by viewer stay hidden.

## Shared component inventory
- `user_attribute_service` invite metadata: reuse to calculate inviter relationships without new schema.
- `account_nav` partial: add "Members" link for authenticated members.
- CSS tokens (`card`, `stack`, `muted`, `meta-chip`) already power cards/badges; extend with a lightweight `members-grid` utility for responsive layout.
- Pagination helper from `/admin/profiles`: reuse logic for `prev/next` URLs but render them inside a members-specific component.

## User flow
1. Member selects "Members" in the nav.
2. Page loads cards for eligible profiles (public + invited) with filters blank.
3. Member enters part of a username or email, presses Apply, sees filtered results.
4. Click on a card opens the profile page appropriate for the viewer role.
5. Pagination controls allow browsing older entries; empty states explain when filters hide everyone or no one is public yet.

## Success criteria
- Authenticated member sees at least one card when public users exist; private profiles remain hidden unless invited.
- Filters narrow the dataset as expected; pagination maintains filter query params.
- Admins see the same count they would in `/admin/profiles` and can jump into admin detail via the card.
- Layout is responsive (cards break to single column <640px) and uses existing design tokens.
- No new database schema; feature reuses existing services and tests via manual QA.
