## Problem
Members can’t see how welcome invites propagate through their community. Without a visual map of 1st-, 2nd-, and 3rd-degree connections, it’s hard to understand reach or spot who needs a nudge.

## User Stories
- As an inviter, I want to see everyone I directly welcomed so I can follow up with them.
- As a community organizer, I want to view 2nd- and 3rd-degree connections to understand how the network is growing.
- As an invitee, I want to know who invited me and who they invited to feel the chain of support.

## Core Requirements
- Provide a page that displays invite relationships up to three degrees from the signed-in user.
- Clearly label the degree (1st, 2nd, 3rd) for each person shown.
- Support branching when a person invited multiple others.
- Offer navigation entry (button near “Share a request”) to reach the map.

## User Flow
1. Signed-in user clicks the new “Invite map” button near “Share a request.”
2. App loads a server-rendered page with a tree view anchored on the user.
3. User scans labeled branches showing 1st-, 2nd-, and 3rd-degree connections.
4. User can return to requests or follow links from the map (if provided later).

## Success Criteria
- All users with invite relationships see the correct three-degree tree without errors.
- Empty-state guidance appears when the user has no outgoing invites.
- Average page load remains comparable to existing invite pages (no major performance hit).
