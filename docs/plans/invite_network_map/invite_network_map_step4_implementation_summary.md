## Feature: Invite Network Map

### Status Overview
- Stage 1 – Data contract for invite graph: *Completed*
- Stage 2 – Template + route skeleton: *Completed*
- Stage 3 – Graph assembly logic: *Completed*
- Stage 4 – UI rendering + styling: *Completed*
- Stage 5 – Entry point & empty states: *Completed*
- Stage 6 – QA & documentation update: *Completed*

### Notes
- Added `invite_graph_service` module with `InviteGraphNode` data structure and helper signature to anchor the graph contract.
- Routed `/invite/map` to a new template that renders invite trees recursively with degree labels.
- Implemented invite graph builder that walks three degrees of relationships via user attributes, guards against cycles, and sorts children for stable rendering.
- Styled the tree view for readability with connector lines, badges, and responsive behavior.
- Added navigation entry near “Share a request” and empty-state guidance pointing users to create their first invite when no data is available.

### Tests
- `tests/services/test_invite_graph_service.py`
- `pytest` *(fails: command not found in this environment)*

### Manual Verification
- Pending: load `/invite/map` in browser to confirm tree renders with real data and empty state; verify request page buttons.

### Testing Plan
- Unit tests for invite graph helper (Stage 3).
- Manual verification for layout, responsiveness, and navigation (Stages 4–6).
