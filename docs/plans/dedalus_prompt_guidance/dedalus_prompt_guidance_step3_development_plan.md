# Dedalus Prompt Guidance – Step 3 Development Plan

## Stage 1 – Prompt Template Update
- **Goal:** Define the constrained verification prompt text that enforces `OK:`/`ERROR:` structure, tool awareness, and length.
- **Changes:** Update `_verify_dedalus_api_key` to send an explicit prompt mentioning WhiteBalloon, Mutual Aid Copilot, expected tools (`audit_auth_requests`), and the response format. Add helper constants/tests for max length.
- **Verification:** Trigger the verification endpoint in dev (mock via CLI) and inspect log to ensure responses follow the template.
- **Risks:** Over-constrained prompt may fail if Dedalus updates models; keep instructions clear but flexible.

## Stage 2 – Response Parsing & Logging
- **Goal:** Detect structured responses (status + tool list) and store them cleanly.
- **Changes:** Add parser that extracts status (`OK`/`ERROR`), summary text, and mentioned tools from Dedalus replies. Store parsed fields in the log entry (new columns or derived fields) so the activity page can display them cleanly.
- **Verification:** Unit-ish test via REPL feeding sample strings; ensure parser handles malformed cases.
- **Risks:** Parser might misclassify edge cases; default to raw response if parsing fails.

## Stage 3 – Admin UI Enhancements
- **Goal:** Highlight structured status/tool info in `/admin/dedalus/logs`.
- **Changes:** Update template to show a success/error badge using parsed status and list tools (if present). Ensure log entries show the concise summary at a glance, with full prompt/response still available.
- **Verification:** Load the activity page with sample entries and confirm new badges/tool list render.
- **Risks:** None major; ensure backward compatibility for old entries lacking structured fields.

## Stage 4 – Guardrails & Fallback Copy
- **Goal:** Provide helpful messaging if Dedalus doesn’t follow the format.
- **Changes:** Detect missing `OK:/ERROR:` prefix; if absent, mark status as `unknown` and show a warning alert in the log entry. Optionally rerun the verification or display guidance to the admin.
- **Verification:** Simulate a non-conforming response and ensure the UI surfaces the warning without breaking.
- **Risks:** Could annoy admins if false positives occur; keep fallback gentle.
