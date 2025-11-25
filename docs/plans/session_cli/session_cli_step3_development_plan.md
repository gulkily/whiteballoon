# Session CLI – Development Plan

1. **Typer Command Scaffolding**
   - Dependencies: Step 2 description.
   - Changes: Add a `session` Typer group in `tools/dev.py`; wire CLI context to database session.
   - Testing: `./wb session --help` and `./wb session list` (stub output).
   - Risks: Loading app context incorrectly; mitigate by reusing existing get_engine/session helpers.

2. **List Command Implementation**
   - Dependencies: Stage 1 scaffold.
   - Changes: Query `AuthenticationRequest` joined with `User`/`UserSession`; format output (tabular columns: ID, username, status, created, code, expires).
   - Testing: Manual CLI call; ensure pending/approved/expired show correctly; handle “no pending requests”.
   - Risks: Long output unreadable; mitigate with simple formatting and optional `--all/--pending` filters.

3. **Approve/Deny Command**
   - Dependencies: Stage 2 listing validated.
   - Changes: Implement `session approve <id> [--approver <username>]` calling `approve_auth_request` and promoting pending requests; optional `session deny <id>` marking status DENIED + cleaning sessions.
   - Testing: Manual CLI flows (approve & deny) verifying DB state and request promotion; check for friendly errors (missing ID, already processed).
   - Risks: Partial promotion failures; mitigate with transaction boundaries and clear messaging.

4. **Docs & Cleanup**
   - Dependencies: Commands functional.
   - Changes: Update README/cheatsheet/spec with CLI usage examples; ensure Step 4 summary captures implementation; run lint/format (if any).
   - Testing: Documentation review; `git grep session list` to ensure references updated.
   - Risks: Documentation drift; mitigate with final checklist aligning CLI output + docs.
