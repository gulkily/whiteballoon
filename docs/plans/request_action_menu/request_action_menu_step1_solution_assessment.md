# Request/Comment Action Menu — Step 1 Solution Assessment

**Problem**: Admin-only actions (pin/unpin, mark complete, promote, etc.) currently appear as standalone buttons on request/comment cards, causing UI clutter and making it hard to add new controls without breaking layout consistency.

## Option A – Pure CSS disclosure (details/summary) per card
- Pros: No JavaScript required; leverages native `<details>` toggling; simplest integration.
- Cons: Limited styling control across browsers; no shared state (can’t auto-close when another menu opens); `summary` text/icon placement is inflexible, making it harder to match existing chip/button aesthetics.

## Option B – Shared template partial + lightweight JS toggle
- Pros: Centralizes markup (icon button + menu list) for reuse by requests and comments; JS can manage focus, close-on-escape, and single-open behavior; easy to add analytics hooks.
- Cons: Requires new JS module + event wiring; needs accessibility work (aria roles, keyboard support).

## Option C – Global toolbar (dedicated admin panel per card)
- Pros: Keeps cards visually clean by rendering admin controls in a consistent panel beneath each item; no dropdown interactions.
- Cons: Still consumes vertical space; users must scan separate sections; doesn’t solve control proliferation, just relocates it; difficult to add context-specific actions without conditional layout logic.

## Recommendation
Option B. A reusable partial backed by a small JS toggle offers the best balance of UX polish, accessibility, and extensibility. We can render a single icon button per card, reuse the same menu structure for requests/comments, and progressively enhance behavior (click outside to close, keyboard navigation) without complicating the base templates. This also creates a natural home for future actions beyond pinning.
