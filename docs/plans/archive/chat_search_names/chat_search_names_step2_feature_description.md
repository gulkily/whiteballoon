# Chat Search Names – Step 2 Feature Description

## Problem
Chat search results on the request detail page display `@username` and link to the comment anchor, while the main comment list shows friendly display names linking to profiles. This inconsistency confuses admins, especially when Signal personas use aliases.

## User stories
- As an admin, I want the identity display in search results to match the comment list so I can recognize who wrote the message instantly.
- As a Signal operator, I want the display name link to open the profile, just like the comment list does, while still being able to jump to the comment via timestamp.
- As an accessibility reviewer, I want the identity information structured consistently (name + tooltip) across the page.

## Core requirements
1. Search result entries show the commenter’s display name (if available) with a tooltip containing `@username`, linking to `/people/<username>`.
2. The timestamp remains the anchor to `#comment-<id>` so users can still jump to the comment in the request.
3. Fallback to `@username` when no display name exists.
4. Keep existing topic chips/body/href structure; no backend API changes beyond reusing the display-name map.

## User flow
1. User performs a chat search.
2. Results show each entry with the display name link (profile) and timestamp link (jump to comment).
3. Clicking the name opens the profile in a new page; clicking the timestamp scrolls within the request.

## Success criteria
- Identity lines in search results visually match the comment list.
- Tooltip/ARIA for usernames still exists.
- No regressions for existing search functionality.
