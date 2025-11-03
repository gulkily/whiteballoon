# Auto Registration Session — Step 3 Development Plan

1. **Stage 1: Invite token schema/config check**
   - Dependencies: Existing `InviteToken` model in `app/models.py`.
   - Changes: Add `auto_approve` boolean (default `True`) or repurpose `token_type` to capture auto-approval intent; migrate existing tokens accordingly.
   - Testing: Manual DB inspection, unit test for default flag.
   - Risks: Migration conflicts; forgetting to backfill existing tokens.

2. **Stage 2: Registration auto-approval logic**
   - Dependencies: Stage 1 flag available; registration flow in `auth_service.create_user_with_invite`.
   - Changes: After user creation, if the invite has `auto_approve`, mark the user fully authenticated, issue full session, and update invite usage logs.
   - Testing: Manual registration with auto-approve token; ensure non-auto tokens still produce half-auth session.
   - Risks: Accidentally auto-approving when flag missing; bypassing security checks.

3. **Stage 3: CLI/Docs updates**
   - Dependencies: Stages 1-2.
   - Changes: Update `create-invite` CLI (tools/dev.py) to surface or override `auto_approve`; document new behavior in README/code tour.
   - Testing: `./wb create-invite --help`; ensure help text mentions auto-approval and default behavior.
   - Risks: CLI help drifting; documentation gaps.

4. **Stage 4: Audit/logging enhancements**
   - Dependencies: Stage 2 logic.
   - Changes: Record auto-approval events (DB log or structured logging) for later review.
   - Testing: Manual log inspection; confirm suppressed for non-auto approvals.
   - Risks: Logging noise; missing context for audits.

5. **Stage 5: QA + regression checks**
   - Dependencies: Stages 1-4 complete.
   - Changes: Execute manual flow for both auto and manual invites; ensure tests updated; maintain docs.
   - Testing: `pytest`; smoke-tests.
   - Risks: Missed edge cases; inconsistent docs.
