# AI Chat Query – Pilot QA Checklist

## Scope
Run this checklist with a 6–8 person cohort that includes at least two CLI-first operators and two web-first members.

## Pre-flight
- `/api/chat/ai` responding locally with HTTP 200s for a known prompt.
- `.env` contains `DEDALUS_API_KEY` (for future tuning) even though current release is deterministic.
- `storage/logs/chat_ai_events.log` writable so telemetry persists.
- Communicate the opt-out marker (`#private`) to all pilot users before kick-off.

## Manual QA
1. **CLI loop**  
   - Run `./wb chat ai --prompt "housing follow ups this week"` as an admin user.
   - Confirm the answer lists ≥2 citations and `Sources:` links open request/comment pages.  
   - Repeat with `#private` in the prompt to ensure the log row redacts the question.
2. **Web panel basic flow**  
   - Navigate to `/requests/channels`, ask “show unread chats from today” in the Ask AI panel.  
   - Verify the spinner appears, response renders in the transcript, and citations show as an ordered list.
3. **Guardrail flow**  
   - Ask “Summarize medical claims data” (something out of scope) and confirm the guardrail message surfaces both in the transcript and below it.
4. **Auth boundary**  
   - Sign out, refresh `/requests/channels`, and confirm the panel collapses into the muted “Sign in” notice with no network calls fired.

## Success criteria sampling
- Pull 5 random responses per tester and ensure ≥70% include a working link back to a request/comment.
- Measure latency: capture `latency_ms` from the JSONL log and confirm median <4000ms during the pilot window.
- Weekly survey: ask “Did the AI chat answer your question?” and tally ≥80% “yes”.
- Adoption goal: at least 30 unique user IDs in the log with ≥3 prompts each.

## Instrumentation checks
- Tail the log for schema regressions (`jq '.' storage/logs/chat_ai_events.log | tail`).
- Alert if `status=guardrail` ratio exceeds 25% so we can revisit prompts.

## Feedback capture
- Collect pilot feedback via `/feedback/ai-chat` (existing form) and tag entries with `ai_chat_pilot`.
- Aggregate themes + action items into `docs/plans/ai_chat_query/pilot_notes.md` if follow-ups emerge.
