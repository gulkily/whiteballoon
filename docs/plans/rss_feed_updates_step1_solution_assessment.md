# RSS Feed Updates – Step 1 Solution Assessment

- **Problem statement**: Users and admins need a low-friction way to monitor new requests and updates through RSS without logging into the UI constantly.

## Option A – Single public RSS feed
- **Pros**
  - Fastest to ship: reuse the existing public request listing and expose it as `/feeds/requests.xml`.
  - Zero auth complexity, so readers can subscribe immediately.
- **Cons**
  - Cannot include member-only or admin-only requests, so it fails the “any type of user” requirement.
  - Hard to personalize (filters, per-user scopes), making the feed noisy for admins with many invites.

## Option B – Tokenized per-user RSS endpoints
- **Pros**
  - Respect existing permission scopes by issuing per-user secret tokens embedded in the feed URL; admins can see everything they already can, while regular members only see their allowed slice.
  - Enables multiple feeds (e.g., “all requests,” “my invites,” “admin triage”) by reusing the same feed-builder with different filters.
  - Aligns with how most RSS readers handle private feeds, so adoption friction stays low.
- **Cons**
  - Requires token management (generation, revocation, rotation) and middleware that authenticates RSS requests without cookies.
  - Must harden rate limiting because URLs become bearer tokens that can leak.

## Option C – Scheduled export to static RSS files
- **Pros**
  - Generates feeds offline (via `./wb` or a background job) and publishes static XML under `data/public_sync/`, avoiding runtime auth logic.
  - Mirrors the existing sync/export workflow, so operators can reason about delivery with familiar tooling.
- **Cons**
  - Static exports can lag behind real-time activity unless jobs run very frequently.
  - Publishing per-user static feeds adds storage churn and token distribution headaches similar to Option B without the responsiveness.

## Recommendation
- **Go with Option B (tokenized per-user RSS endpoints).** It directly serves the story (“any type of user and admin”) by honoring existing access scopes while keeping UX simple—copy a secret RSS URL into any reader and get live updates that match what the web app already shows. The token/auth work is contained, and the feed builder can still expose a pared-down public variant later if needed.
