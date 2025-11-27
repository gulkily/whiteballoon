# Half-Auth Shadow Publish – Development Plan

1. **Schema & Model Prep**
   - Dependencies: Solution assessment + feature description approved.
   - Changes: Confirm `HelpRequest.status` usage for staging (e.g., enforce `pending` semantics) without schema changes; outline promotion fields (timestamps, approver) in spec.
   - Testing: Model/unit sketch (no runtime changes). Manual review with spec to ensure fields cover status, timestamps, user linkage.
   - Risks: Schema churn; mitigate with minimal fields and forward-compatible design.

2. **Backend Staging Pipeline**
   - Dependencies: Stage 1 schema design finalized.
   - Changes: Implement repository/service functions to create, list, and delete staged requests; update authentication approval flow to promote staged items atomically; block direct writes to live tables for half-auth sessions.
   - Testing: Unit/integration tests (if available) or manual verification via CLI/HTTP requests; ensure approval promotes staged data and clears staging entries.
   - Risks: Data loss or double promotion; mitigate with transaction boundaries and idempotent promotion logic.

3. **UI Integration & Feedback**
   - Dependencies: Stage 2 backend endpoints working.
   - Changes: Adjust pending dashboard to display staged items from server; update JS to fetch staged drafts; update interactive feed to include newly promoted entries after approval; ensure fully authed users don't see staging UI.
   - Testing: Browser smoke tests covering pending view, approval, post-approval refresh; verify staged items invisible to others pre-approval.
   - Risks: Confusing UX during transition; mitigate with clear messaging and state checks.

4. **Docs & Cleanup**
   - Dependencies: Functionality complete.
   - Changes: Update `docs/spec.md`, README, and plans with shadow publish lifecycle; remove any obsolete draft/local storage references; ensure new schema documented.
   - Testing: Documentation review; `git grep` for outdated terms.
   - Risks: Documentation drift; mitigate with final checklist per spec guidelines.
