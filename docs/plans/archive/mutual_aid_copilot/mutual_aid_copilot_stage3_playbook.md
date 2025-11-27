# Mutual Aid Copilot – Stage 3 Implementation Playbook

## Capability: MCP Tool Catalog
1. Inventory admin workflows (request audit, privacy toggle, connector recommendation, sync prep, invite context). (½ hr)
2. Draft tool schemas (input/output) in docs + JSON for Dedalus registration. (1 hr)
3. Implement FastAPI endpoints/CLI wrappers conforming to schemas. (≤50 LoC each)
4. Register tools with Dedalus sandbox; validate authentication using instance API key. (1 hr)
5. Verification: Dedalus test harness runs each tool with sample payloads; ensure 200 responses and privacy filters applied.

## Capability: Admin Credential Manager
1. Add `DEDALUS_API_KEY` to config + .env docs (done). (30 min)
2. Create `/admin/dedalus` route + template to set/clear key (done). (n/a – tracked in code)
3. Add server-side validation (length/prefix) and success/error messaging. (30 min)
4. Ensure `.env` updates cause settings cache refresh without restart. (done). Verification: manual test.

## Capability: Copilot UI Surface
1. Design UI (chat pane + quick actions) embedded in admin panel. (45 min)
2. Build frontend component that captures admin prompt and invokes backend endpoint. (1 hr)
3. Backend endpoint calls Dedalus REST API with stored key, including context packaging helper. (1 hr)
4. Stream results (text + tool outputs) back to UI; handle errors gracefully. (1 hr)
5. Verification: manual e2e test plus mocked unit test for backend call.

## Capability: Context Packaging Layer
1. Implement serializer that fetches request/comment/user data restricted to allowed scopes. (45 min)
2. Tag each payload with privacy metadata and include only necessary fields (first name, public notes, etc.). (45 min)
3. Add guard rails: reject attempts to send private data; log when contexts exceed limits. (30 min)
4. Verification: unit tests feeding mixed-scope data ensure only public/explicit segments are sent.

## Capability: Usage Telemetry & Logging
1. Define log schema (tool_name, request_id, duration, outcome). (30 min)
2. Hook into Dedalus response handler to emit logs + optional DB records. (45 min)
3. Provide daily usage summary command for admins. (45 min)
4. Verification: run smoke tests, confirm logs appear; unit tests for logging helpers.

## Capability: Launch & User Testing Toolkit
1. Write onboarding doc guiding communities through setting up Dedalus API keys and enabling copilot. (45 min)
2. Prepare feedback form + schedule testing sessions. (30 min)
3. Implement feature flag to enable/disable copilot per instance (config + UI toggle). (45 min)
4. Verification: onboarding with two pilot houses; collect metrics + iterate.

## Rollout & Ops
- Feature flag `MUTUAL_AID_COPILOT_ENABLED` default false; set true per instance once verified.
- Logging dashboards (maybe simple CSV/JSON) to share metrics with Dedalus weekly.
- Fallback: disable copilot flag and rely on existing manual admin tools if Dedalus unavailable.

## Instrumentation & Alerts
- Add structured logs for each Dedalus call with success/failure.
- Optional Sentry/Logfire hooks for exceptions.
- Daily cron to summarize usage + alert if error rate >5%.
- Standardize timestamp displays using `friendly_time` filter + raw tooltip for consistency across UI.
