# AI Chat Query – Step 3: Development Plan

1. **Clarify API contract for AI chat endpoint**  
   - Dependencies: existing `/chat/respond` FastAPI module, Step 2 requirements.  
   - Expected changes: define new payload/response schema (`POST /chat/ai` with `conversation_id`, `prompt`, `context_scope`, returns `messages`, `citations[]`); note auth policies and rate limits.  
   - Verification: draft OpenAPI snippet + example request/response, review with backend lead.  
   - Risks: scope creep into full convo history storage; ambiguity about multi-tenant context.  
   - Components touched: FastAPI router, shared schema module.  

2. **Extend retrieval + prompt composer**  
   - Dependencies: Stage 1 contract, existing Dedalus retriever and embedding store.  
   - Expected changes: add helper `build_ai_chat_context(user, conversation_id, prompt) -> RetrievedContext`; support multi-source aggregation and citation metadata; implement guardrails (max tokens, fallback when no results).  
   - Verification: unit tests for retrieval filters, manual dry run using fixture requests/chats.  
   - Risks: latency spikes when querying multiple collections; missing citation mapping when objects are deleted.  
   - Components touched: `wb/dedalus/retrieval.py`, prompt template definitions.  

3. **Implement `/chat/ai` FastAPI route**  
   - Dependencies: Stage 2 helper, Stage 1 schema alignment.  
   - Expected changes: new controller that validates auth scopes, calls composer, streams model output, and emits structured citations; log interactions via existing analytics hook.  
   - Verification: local API call via `curl` + mocked user to confirm responses and secure data boundaries.  
   - Risks: streaming vs buffering decisions; logging sensitive text inadvertently.  
   - Components touched: `app/api/routes/chat.py`, logging utilities.  

4. **Update CLI (`wb chat ai`)**  
   - Dependencies: Stage 3 endpoint available.  
   - Expected changes: add subcommand `wb chat ai [--conversation <id>]`; handle conversational loops with truncated history; render AI + user messages using existing chat bubble renderer, surface citations as numbered refs.  
   - Verification: manual CLI session covering question, follow-up, and citation link open; regression check existing `wb chat` flows.  
   - Risks: history persistence across runs; terminal width issues for citations.  
   - Components touched: `wb/cli/chat.py`, shared CLI session manager.  

5. **Add web chat panel UI**  
   - Dependencies: Stage 3 endpoint, Stage 2 retrieval context contract.  
   - Expected changes: vanilla JS module (e.g., `static/js/chat-ai-panel.js`) that renders an input, transcript container, and spinner using existing DOM templates; wire it into the chats page without introducing new third-party frameworks; reuse chat bubble classes and link handling; call `/chat/ai`.  
   - Verification: local dev server manual test on desktop + mobile widths, confirm citations open correct modals/pages.  
   - Risks: layout crowding on smaller screens; WebSocket vs HTTP mismatch (consider fetch + SSE fallback).  
   - Components touched: `templates/chats/*.html`, `static/js/chat-ai-panel.js`, shared API client helpers.  

6. **Telemetry + guardrail instrumentation**  
   - Dependencies: Stages 3–5 in place.  
   - Expected changes: log per-query metrics (latency, sources, outcome codes) to analytics pipeline; add structured event names for CLI + web; capture opt-out for sensitive topics.  
   - Verification: inspect logs locally / staging to ensure records emit; run synthetic failure to confirm guardrail messaging.  
   - Risks: PII leakage if we over-log prompts; metrics noise if conversation IDs churn.  
   - Components touched: analytics middleware, logging config, client event dispatchers.  

7. **Pilot QA + success criteria review**  
   - Dependencies: Stages 1–6.  
   - Expected changes: assemble checklist covering success metrics (citation % samples, latency measurement, user feedback form); prep instructions for pilot cohort.  
   - Verification: run smoke tests, capture initial survey template, document known issues.  
   - Risks: unclear owner for monitoring; delays if telemetry not wired.  
   - Components touched: docs (`docs/plans/README` updates), QA checklist templates.  
