# Members list page — Step 1: Solution Assessment

**Problem**: Members cannot browse other community members today; only admins have `/admin/profiles`, so we need a member-friendly directory that respects privacy scopes without duplicating logic.

## Option A — Reuse admin directory stack with shared partials
- **Pros**
  - Minimal new SQL/query logic; reuse `admin_profile_directory` filters + pagination.
  - Guarantees parity with admin dataset (less drift) while hiding privileged controls.
  - Faster delivery; mostly templating + permission gate wiring.
- **Cons**
  - Requires carefully sharing template components to avoid leaking admin-only actions.
  - Member view still tied to admin-style table layout (less room for bespoke UX).

## Option B — Build dedicated `/members` route + template
- **Pros**
  - Tailored UX for members (cards, avatars, CTA buttons) without admin constraints.
  - Can enforce privacy filters inside a purpose-built query layer.
- **Cons**
  - Duplicates filtering logic unless refactored; more code to maintain.
  - Higher implementation cost; risk of diverging data/bug parity with admin view.

## Option C — Expose filtered API + client-side enhancement
- **Pros**
  - Opens path for richer experiences (instant search, future mobile app reuse).
  - Server still controls auth; API can reuse admin query logic.
- **Cons**
  - Requires new API contract + JS layer; unnecessary complexity for MVP.
  - Adds caching/pagination challenges sooner.

## Recommendation
Pursue **Option A**: share the existing admin directory pipeline but introduce a members-only wrapper (`/members`) that filters rows based on `sync_scope`/inviter relationships and strips privileged controls. This keeps implementation lean, ensures data consistency, and meets MVP expectations quickly.
