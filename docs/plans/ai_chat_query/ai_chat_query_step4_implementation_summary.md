# AI Chat Query – Step 4 Implementation Summary

## Stage 1 – API contract + router scaffolding
- Changes: Added `app/routes/chat_ai_api.py` with request/response schemas, rate-limit constants, and a placeholder `/api/chat/ai` route wired into `app/main.py` via the new module export.
- Verification: Instantiated the new Pydantic payload/response models in a Python shell to confirm defaults, serialization, and field validation behaved as expected.
- Notes: Endpoint currently raises HTTP 501 until retrieval + generation logic land in later stages.

## Stage 2 – Retrieval + prompt context helper
- Changes: Introduced `app/services/chat_ai_service.py` to aggregate help-request and comment citations with scope-aware filtering, keyword extraction, and guardrail messaging; registered the service in `app/services/__init__.py`.
- Verification: Opened a local SQLModel session and executed `build_ai_chat_context` with an admin user in a Python shell to confirm it returns live citations without raising errors.
- Notes: Context results stay purely deterministic for now; later stages will translate them into chat responses.

## Stage 3 – Implement `/api/chat/ai`
- Changes: Replaced the placeholder route with logic that builds contextual citations, composes a deterministic assistant reply, and logs usage metadata; responses now include numbered user/assistant messages plus guardrail text when no matches exist.
- Verification: Called `chat_ai_query` directly inside a Python shell with a real SQLModel session and ensured it returned a conversation ID, assistant response, and citation list.
- Notes: Still synchronous HTTP; streaming/backpressure can be revisited after the first release.

## Stage 4 – Add `wb chat ai` CLI experience
- Changes: Added `CHAT_AI_CLI_MODULE` wiring plus a new subcommand that launches `app.tools.chat_ai_cli`, which impersonates a chosen username, runs prompts through the retrieval helper, and formats answers plus citation links inline.
- Verification: Ran `./wb chat ai --prompt 'housing updates'` to confirm the new CLI prints summarized answers and source links without errors.
- Notes: CLI uses direct DB access today; HTTP auth sessions can layer on later if needed.

## Stage 5 – Web AI panel
- Changes: Inserted an “Ask AI” panel on the request channels page with new markup, vanilla JS (`static/js/chat-ai-panel.js`) for calling `/api/chat/ai`, and scoped styles inside `static/skins/base/30-requests.css`.
- Verification: Rendered `templates/requests/channels.html` through the shared Jinja environment with a stub request/session to confirm the panel markup appears (`data-chat-ai-panel` present).
- Notes: Browser testing still recommended to validate fetches and auth cookies end-to-end.

## Stage 6 – Telemetry + guardrail instrumentation
- Changes: Added `app/services/chat_ai_metrics.py` to write JSONL usage rows with opt-out support (`#private` marker), wired logging into the FastAPI route and CLI helper, and began persisting events under `storage/logs/chat_ai_events.log`.
- Verification: Ran `./wb chat ai --prompt 'telemetry stage'` and inspected the new log file to confirm a structured entry was recorded.
- Notes: Web callers inherit the same opt-out behavior automatically.

## Stage 7 – Pilot QA + success checklist
- Changes: Consolidated all planning docs into `docs/plans/ai_chat_query/`, documented the pilot QA checklist (`ai_chat_query_pilot_checklist.md`), and indexed the folder for discoverability in `docs/plans/README.md`.
- Verification: Rendered the checklist locally to ensure formatting and steps cover the success criteria, and confirmed the new folder appears in the planning index.
- Notes: Capture pilot feedback per the checklist and open follow-up tickets rather than extending Stage 4.
