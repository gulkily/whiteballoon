## Stage 1 – Adjust AI response text composition
- Changes: Updated the AI response message to summarize counts and point to Sources instead of listing every title.
- Verification: Not run (per AI_PROJECT_GUIDE). Suggested manual check: ask a question in Request Channels and confirm the reply is a short summary with Sources unchanged.
- Notes: None.

## Stage 2 – Align CLI output with the new response summary
- Changes: Replaced the CLI's full title list response with the same concise summary and pointer to Sources.
- Verification: Not run (per AI_PROJECT_GUIDE). Suggested manual check: run `./wb chat ai --prompt "<question>"` and confirm the reply is a short summary with Sources listed below.
- Notes: None.
