# Dedalus Chat Index Logging — Step 1 Solution Assessment

**Problem**: When operators run `wb chat index` with `--llm`, Dedalus usage isn’t logged in `/admin/dedalus/logs`, making it impossible to audit model interactions or surface failures in the admin UI.

## Option A – Wrap the LLM classifier with `start_logged_run`/`finalize_logged_run`
- Pros: Minimal changes localized to `request_chat_index.py`; reuses existing logging infrastructure; captures precise prompts/responses per run.
- Cons: Need to thread user/request context into the log call; ensure logging doesn’t break the CLI if Dedalus logging fails.

## Option B – Log at CLI level only
- Pros: Simple to add a log entry at the start/end of the CLI, without touching the classifier.
- Cons: Doesn’t record per-comment prompts/responses, only high-level runs; may miss granular dedalus interactions if multiple requests are processed.

## Option C – Defer logging entirely (document separately)
- Pros: No code change.
- Cons: Doesn’t solve the auditing gap; admins still can’t see chat index runs in the log viewer.

## Recommendation
Option A. Instrument the Dedalus-powered classifier inside `request_chat_index.py` so each LLM invocation starts a logged run (with request/comment context) and finalizes it with status + response metadata. This keeps the log consistent with other Dedalus features, surfaces runs in `/admin/dedalus/logs`, and captures per-comment prompts.
