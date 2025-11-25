# User Attributes Schema — Step 3 Development Plan

1. **Stage 1: Schema definition and migration scaffold**
   - Dependencies: Existing database migration tooling.
   - Changes: Introduce `user_attributes` SQLModel with fields (`id`, `user_id`, `key`, `value`, `created_at`, `updated_at`, `created_by_user_id`, `updated_by_user_id`); draft migration adding table with unique (`user_id`, `key`) constraint and supporting indexes.
   - Testing: Manual migration run in dev environment; ensure table appears with expected schema.
   - Risks: Migration conflicts in shared environments; forgetting to backfill timestamps.

2. **Stage 2: Repository/helpers for attribute access**
   - Dependencies: Stage 1 table/model in place.
   - Changes: Implement helper functions/services for get/set/delete attributes, automatically populating `created_at`, `updated_at`, and actor IDs from session context.
   - Testing: Unit tests or manual REPL checks storing and fetching attributes for a user; validate uniqueness enforcement.
   - Risks: Missing transaction boundaries leading to partial writes; inconsistent timestamp updates.

3. **Stage 3: Capture inviter attribute write path**
   - Dependencies: Stage 2 helpers available; invite creation flow identified.
   - Changes: During invite acceptance/user creation, persist `invited_by_user_id` attribute using helper; ensure existing logic continues to work when attribute absent.
   - Testing: Manual signup flow with known inviter; confirm attribute stored; verify read helpers on profile/analytics path.
   - Risks: Invite flow refactor complexity; incomplete backfill for existing users (call out as follow-up if deferred).

4. **Stage 4: QA + documentation**
   - Dependencies: Stages 1-3 complete.
   - Changes: Smoke test attribute lifecycle (create/update/delete) in development; document new table and helper usage for future attributes; note any backlog tasks (e.g., backfilling legacy data).
   - Testing: Manual interactive checks plus unit tests if feasible; confirm no regressions in existing invite functionality.
   - Risks: Missed permission checks on attribute writer; documentation drift if team conventions change.
