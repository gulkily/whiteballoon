# Peer Auth Feature Flags · Step 3 Development Plan

## Stage 1 – Config plumbing + env docs
- **Goal**: Expose the two feature flags (`feature_peer_auth_queue`, `feature_self_auth`) in `Settings` and `.env.example`.
- **Dependencies**: None.
- **Changes**: Add typed attributes to `Settings` pulling from `WB_FEATURE_PEER_AUTH_QUEUE` / `WB_FEATURE_SELF_AUTH`; update `.env.example` docs; reset config cache helper to pick up new fields.
- **Verification**: `python - <<'PY' from app.config import get_settings; print(get_settings().feature_peer_auth_queue)` style smoke; ensure `.env.example` entries match naming.
- **Risks**: Typos causing missing env reads; keep var names consistent with Step 2 doc.

## Stage 2 – Toggle guards in peer-auth UI/routes
- **Goal**: Gate the peer approval inbox, ledger page, and associated menu links behind the peer queue flag.
- **Dependencies**: Stage 1 config fields.
- **Changes**: Wrap `/peer-auth` routes, ledger endpoints, menu/admin links, and templates with flag checks. When disabled, hide UI entry points and return 404/403 responses if endpoints hit directly. Add banner text indicating feature disabled when flag false but ledger page accessed (e.g., for admins verifying state).
- **Verification**: Flip env flag locally, restart server, confirm `/peer-auth` link disappears and hitting URL returns 404; re-enable and ensure functionality returns.
- **Risks**: Forgetting a surface (e.g., menu vs admin panel) leading to broken link; mitigate by grepping for `/peer-auth` references.

## Stage 3 – Self-auth flow gating on login_pending
- **Goal**: Add optional self-auth UI/logic to the half-auth login page using the same 6-digit code.
- **Dependencies**: Stage 1 config + existing auth service.
- **Changes**: Update `templates/auth/login_pending.html` and any backing routes to show a self-auth form/button when `feature_self_auth` true. Implement POST handler (or reuse existing verify endpoint) to accept the code locally, bypassing peer queue while logging the action. When flag off, maintain current instructions.
- **Verification**: With flag on, walk through login -> half-auth -> self-auth form completes and user becomes fully authenticated without peer approval; with flag off, confirm form absent.
- **Risks**: Allowing self-auth could bypass security if misconfigured; ensure only sessions tied to the code can self-complete and add throttling/validation reuse from `auth_service`.

## Stage 4 – Messaging + telemetry updates
- **Goal**: Ensure admins/reviewers see status indicators and that logs capture flag-blocked actions.
- **Dependencies**: Stages 2–3 changes.
- **Changes**: Add banner/snackbar text on `/peer-auth` and ledger pages when disabled, update logging to note when an action was prevented because a flag is off, and adjust support copy on login pending page. Update Step 4 summary accordingly.
- **Verification**: Toggle flags to off state and confirm banners/log messages appear; re-enable and confirm no residual warnings.
- **Risks**: Duplicate logging noise; keep messages brief and structured.
