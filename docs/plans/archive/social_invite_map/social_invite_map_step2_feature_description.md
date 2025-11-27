## Problem
Members cannot currently see how they are connected through invites, so they lack context about who brought them in and which of their own invitees are expanding the community.

## User Stories
- As a member, I want to see the person who invited me and who invited them so I understand my upstream connections.
- As a member, I want to see everyone I invited and the people they invited so I can gauge my downstream impact.
- As a returning member, I want previously computed maps to load instantly so I can revisit the network without waiting.
- As an admin, I want edges to refresh when new invites are accepted so cached maps stay accurate.

## Core Requirements
- Fetch and display all users within 2 degrees above and below the viewer based on invite relationships.
- Present the map in a clear server-rendered layout that distinguishes upstream vs downstream branches.
- Create a cache table keyed by user that stores the serialized 2-degree map and metadata (e.g., generated_at, version).
- Invalidate or refresh a cached map when the viewer’s invite relationships change (new invite, accepted invite, or attribute edit).
- Respect existing auth/session rules so members only see their own map (no ability to inspect arbitrary users).

## User Flow
1. Member visits the social map page from their profile/navigation.
2. System checks the cache table for a fresh map (within defined staleness window) for that user.
3. If cached, deserialize and render the server-side template; otherwise build a new 2-degree graph, store it in the cache, and render.
4. Member reviews the upstream/downstream sections and can follow links to user profiles as needed.
5. When the user invites someone or a pending invite is accepted, invalidate the affected cache entry so the next visit rebuilds it.

## Success Criteria
- Map loads under ~250 ms when served from cache and under ~1 s when rebuilt for networks ≤300 nodes.
- Every user sees both upstream and downstream branches limited to 2 degrees with accurate usernames and invite timestamps where available.
- Cache table entries are created for first-time visits and refreshed automatically when invite relationships change.
- Feature is discoverable via existing navigation (profile or settings) and gated behind standard authentication.
