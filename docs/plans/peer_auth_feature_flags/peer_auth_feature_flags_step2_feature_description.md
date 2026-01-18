# Peer Auth Feature Flags · Step 2 Feature Description

**Problem**: We need to control rollout of the peer verification queue and a new self-auth fallback (where users can finalize login with the same 6-digit code) so admins can stage, monitor, and disable either path without redeploying code.

**User stories**
- As an admin, I want a config flag to disable the peer-auth reviewer queue so I can pause the workflow if we spot abuse or if a community isn’t ready for peer approvals.
- As an admin, I want a separate flag to enable/disable self-auth so we can test the automated path gradually while keeping manual peer verification available.
- As a reviewer, I want the UI to clearly indicate when peer-auth is disabled so I don’t waste time looking for entries that aren’t accessible.
- As an awaiting user, I want the login screen to communicate whether self-auth is available with my 6-digit code so I know whether to wait for a peer or complete it myself.

**Core requirements**
- Introduce two independent feature flags (`WB_FEATURE_PEER_AUTH_QUEUE`, `WB_FEATURE_SELF_AUTH`) exposed via `Settings`/`.env`, defaulting to “off”, and document them in `.env.example` for operators.
- Guard all peer-auth routes/templates/background jobs so that when the peer flag is off, the menu links disappear and endpoints return 404/disabled messaging.
- Gate the half-auth login flow so self-auth actions only appear when the flag is on; when off, continue instructing users to contact a peer reviewer.
- Surface admin-visible indicators (e.g., banner on `/peer-auth`, message on `/admin/peer-auth/ledger`) reflecting the current flag state to avoid confusion.
- Ensure telemetry/logging records when actions are blocked due to feature flags for easier debugging.

**Shared component inventory**
- `templates/peer_auth/index.html` and related CSS – reused but wrapped in conditionals so the entire section hides when the queue flag is false.
- `app/routes/ui/peer_auth.py` and ledger download endpoints – reused; they should short-circuit with HTTP 404/403 when the queue flag is off instead of rendering.
- `templates/auth/login_pending.html` (half-auth screen) – extend it to show self-auth instructions/buttons only when `WB_FEATURE_SELF_AUTH` is enabled; otherwise reuse the existing static message.
- Admin Menu links (`templates/admin/panel.html`, `app/routes/ui/menu.py`) – reused; ensure link lists respect the peer flag before showing the ledger/queue entry points.

**User flow**
1. Admin toggles feature flags via environment or settings UI; application reloads picks up the config.
2. If the peer queue flag is off, users no longer see `/peer-auth` links and hitting the endpoint returns a disabled notice; ledger downloads remain accessible only if flag on.
3. When the self-auth flag is on, the half-auth login page surfaces the “enter code to self-verify” form; when off, it keeps the “contact a peer reviewer” instructions.
4. Reviewers/admins see banner text on relevant pages indicating which features are active to avoid misinterpretation.

**Success criteria**
- Toggling `WB_FEATURE_PEER_AUTH_QUEUE` off removes all peer-auth UI entry points and blocks direct URL access within seconds (after reload) without errors.
- Toggling `WB_FEATURE_SELF_AUTH` on exposes the self-auth form, and at least one monitored session completes without peer assistance during testing.
- Audit logs include explicit entries when actions are blocked due to disabled flags.
- Support team reports zero confusion about feature availability during rollout (measured through internal QA feedback).
