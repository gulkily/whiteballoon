# Dedalus Comment LLM Logging — Step 1 Solution Assessment

**Problem**: `wb chat llm --provider dedalus` triggers Dedalus API usage, but runs never appear in `/admin/dedalus/logs`, leaving admins blind to long-running or interrupted batch executions.

## Option A – Wrap batch executions with `start_logged_run` / `finalize_logged_run`
- Pros: Minimal change footprint (batch loop already centralizes prompts/results); mirrors `request_chat_index` precedent so log viewers behave consistently; captures per-batch metadata (snapshot label, batch size, prompt) without per-comment noise.
- Cons: Loses per-comment visibility if multiple comments share one batch; need to craft representative prompt summary so redactable data isn’t over-shared.

## Option B – Instrument the Dedalus client at per-comment granularity
- Pros: Richest audit trail (exact prompt/response per comment); enables tooling reuse with existing comment-level insights tables.
- Cons: Higher volume of log rows (batch of 10 ⇒ 10 log runs); requires threading individual comment metadata through batching pipeline; more chances for logging failures to slow execution.

## Option C – Log only high-level CLI invocations
- Pros: Trivial to implement at the CLI wrapper (`cmd_comment_llm`); zero risk of leaking comment bodies to logs.
- Cons: Provides no insight into actual LLM prompts, responses, or batch progress; still leaves admins guessing which comments were touched.

## Recommendation
Option A. Capturing one Dedalus log per executed batch balances traceability with manageable volume: admins can correlate batch indices, snapshot labels, and `run_id` with stored analyses, while keeping implementation localized to the batch loop (wrapping each `client.analyze_batch` call). If deeper granularity is later required, we can extend to Option B without reworking the logging infrastructure.
