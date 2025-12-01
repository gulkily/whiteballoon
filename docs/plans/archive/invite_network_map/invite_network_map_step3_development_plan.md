## Stage 1 – Data contract for invite graph
- Dependencies: existing invite data models/API; Step 2 requirements
- Changes: document data needs; ensure backend can provide inviter→invitee mapping limited to three degrees; decide reuse of existing endpoints vs new query helper (no implementation yet)
- Testing: Outline unit test targets (e.g., graph-building helper)
- Risks: Hidden circular invites; performance when fetching nested relationships

## Stage 2 – Template + route skeleton
- Dependencies: Stage 1 decisions
- Changes: New route/controller stub returning fake invite graph; create template structure with placeholder tree layout
- Testing: Plan server-side render smoke test; note manual spot-check
- Risks: Layout complexity; data shape mismatch once real data wired

## Stage 3 – Graph assembly logic
- Dependencies: Stage 1 contract, Stage 2 scaffold
- Changes: Implement backend helper to compute three-degree invite tree; integrate into route
- Testing: Unit tests for helper covering branching, missing data, circular guard
- Risks: Recursive depth errors; performance of repeated DB lookups

## Stage 4 – UI rendering + styling
- Dependencies: Stage 2 template, Stage 3 data
- Changes: Render tree with degree labels, nested lists or similar; add CSS for indentation and branch clarity; responsive tweaks
- Testing: Manual verification across desktop/mobile widths
- Risks: Long names causing overflow; readability for large branches

## Stage 5 – Entry point & empty states
- Dependencies: Stage 4 UI
- Changes: Add “Invite map” button beside “Share a request”; show empty-state messaging when user has no invites; ensure navigation links back to requests/invite workflows
- Testing: Manual navigation test; confirm button visible in relevant contexts
- Risks: Double entry links; confusing state when invites exist but not loaded

## Stage 6 – QA & documentation update
- Dependencies: All prior stages
- Changes: Final pass on copy/styling; document feature in README or appropriate doc if needed; summarize tests performed
- Testing: Execute defined tests; capture manual verification checklist
- Risks: Missing edge cases (e.g., deleted invitees); schedule overrun delaying verification
