# Comment Display Cards – Step 3 Development Plan

## Stage 1 – Shared partial + helpers
- **Goal**: Create a reusable template for rendering comment cards.
- **Dependencies**: Request comment serialization, existing partials (e.g., `requests/partials/comment.html`).
- **Changes**: Extract common markup into `templates/partials/comment_card.html` (or similar) with slots/flags for scope badges and actions; update serialization/contexts to pass the needed data (display name, username, comment anchor, actions list).
- **Verification**: Render request detail page to confirm comments still match previous layout.
- **Risks**: Need to ensure moderation/share buttons remain functional.

## Stage 2 – Apply to chat search + profile pages
- **Goal**: Replace bespoke comment markup in chat search (server fallback) and profile comment index with the shared partial.
- **Dependencies**: Stage 1 partial ready.
- **Changes**: Update `templates/requests/detail.html` search results and `templates/profile/comments.html` to include the partial with compact mode options; adjust CSS variables if needed.
- **Verification**: Manual walkthrough on desktop/mobile; confirm layout consistency and link behaviors.
- **Risks**: Search results currently hydrate via JS—ensure fallback markup still works when JS is disabled.
