# Mobile Navigation & Typography Simplification — Step 2 Feature Description

## Problem
On small screens the header overflows with badges, username, theme toggle, and sign-out, forcing awkward wrapping. Typography tokens stay large, so buttons and headings feel oversized and compete for attention.

## User Stories
- As a mobile user, I want a compact header so primary actions (theme, sign out) stay accessible without scrolling or horizontal drag.
- As an administrator, I want role/status context available but not overwhelming the top of the page.
- As a designer, I want responsive typography tokens so headings/buttons scale gracefully on narrow viewports.

## Core Requirements
- Introduce a mobile nav pattern (drawer or condensed pill stack) that collapses badges + username + theme toggle into an organized group.
- Adjust responsive typography tokens to scale down headings, badges, and button padding on breakpoints ≤768px.
- Preserve quick access to theme toggle and sign-out while respecting tap targets and accessibility.
- Ensure desktop layout remains unchanged.

## User Flow
1. On mobile width, header condenses into a streamlined bar with a toggle/drawer for role info and theme control.
2. User taps the condensed element to reveal role/status details if needed.
3. Typography scale ensures hero headings and buttons appear balanced across breakpoints.

## Success Criteria
- No horizontal overflow in header on devices ≤768px.
- Theme toggle and sign-out remain reachable with ≤2 taps.
- Typography scale passes manual visual inspection on small screens while desktop view is unaffected.
- Manual smoke test confirms focus order and screen-reader announcements remain sensible.
