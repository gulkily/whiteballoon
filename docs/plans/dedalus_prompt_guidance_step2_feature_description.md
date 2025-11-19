# Dedalus Prompt Guidance – Step 2 Feature Description

## Problem
Our "Verify connection" action produces long, generic troubleshooting advice because the prompt doesn’t constrain the model. Admins want a concise success/failure statement logged.

## User Stories
- As an admin, I want the verification log entry to state whether connectivity worked in a single sentence.
- As an auditor, I want optional context (model, timestamp) but not multi-step guides unless an error occurs.
- As a developer, I want to detect the status programmatically (e.g., message starts with `OK:` or `ERROR:`).

## Core Requirements
- Rewrite the verification prompt to demand a structured response: `OK: <short summary>` on success, `ERROR: <short description>` on failure.
- Instruct Dedalus to confirm it recognizes the WhiteBalloon context (e.g., "Mutual Aid Copilot"), list available tools, and state which one it intends to use; log this info along with the status.
- Enforce max response length (e.g., 300 chars) via prompt instructions.
- Extend the log viewer to highlight the structured status (badge or color) for this run type.
- Preserve access to detailed diagnostics only when Dedalus returns errors (e.g., include extra guidance in the `ERROR:` body if needed).

## User Flow
1. Admin clicks “Verify connection.”
2. Backend sends the new constrained prompt (including "tell me which tools you know about") to Dedalus.
3. Dedalus responds with `OK: Verified <timestamp>; tools: audit_auth_requests` (or `ERROR: ...`).
4. Log entry shows the concise response plus tool-awareness note; auditor can expand for full prompt if desired.

## Success Criteria
- Minimum 90% of verification runs return `OK:` responses under 300 chars when the call succeeds.
- Responses enumerate at least one known tool (`audit_auth_requests`) so we know Dedalus recognizes our MCP wiring.
- Error cases still include actionable info prefixed with `ERROR:`.
- The activity log clearly shows the structured status without extra noise.
