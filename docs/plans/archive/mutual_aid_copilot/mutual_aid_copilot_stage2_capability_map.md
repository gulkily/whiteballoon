# Mutual Aid Copilot – Stage 2 Capability Map

| Capability | Scope | Dependencies | Acceptance Tests |
|------------|-------|--------------|------------------|
| MCP Tool Catalog | Define Dedalus MCP schemas for request audit, privacy toggle, connector recommendation, sync prep. | app/config, tools/dev.py, Dedalus API. | All tools callable via Dedalus sandbox with mock data; schema docs generated. |
| Admin Credential Manager | UI + backend to store instance Dedalus API key (.env) with validation. | Admin routes, file-system access, settings cache. | Admin can set/clear key; subsequent requests use updated key without restart. |
| Copilot UI Surface | Reactivate admin UI components (panel, modals, chat) that invoke Dedalus tools. | templates/admin, FastAPI endpoints, Dedalus client library. | Admin can request “audit request #123” and view Dedalus response inline, including tool outputs. |
| Context Packaging Layer | Serialize allowed data (requests/comments/users flagged public) for Dedalus invocation, respecting privacy flags. | Sync/export modules, privacy model, config.skins. | Requests with private scope never leave instance; logs prove compliance. |
| Usage Telemetry + Logging | Capture MCP invocations, success/failure, duration; expose to Dedalus/ops dashboards. | logging config, database (optional), Dedalus callbacks. | Each tool invocation logged with correlation ID; dashboards show daily usage. |
| Launch + User Testing Toolkit | Scripts/docs for onboarding instances, collecting feedback, and toggling features. | README/docs, CLI, invites. | At least 3 external communities onboarded with working copilot; feedback loop established. |

### Dependency Graph
- MCP Tool Catalog is prerequisite for Copilot UI Surface and Context Packaging.
- Admin Credential Manager must exist before MCP calls can run in production.
- Context Packaging relies on privacy model; telemetry layers on top of tool invocation.
- Launch toolkit depends on all prior capabilities to demonstrate end-to-end value.
