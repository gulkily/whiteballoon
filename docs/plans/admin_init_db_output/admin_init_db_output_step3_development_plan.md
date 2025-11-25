# Admin Init-DB Output — Step 3 Development Plan

1. **Stage 1: Instrument database initialization flow**
   - Dependencies: Step 2 spec approved.
   - Changes: Update `wb.py` (or the underlying CLI entry point) to wrap `init_db()` with structured logging (start/end, connection info, table creation summary, error handling). Capture table creation results via `SQLModel.metadata.tables` or engine inspection.
   - Testing: Manual invocation against empty and pre-populated SQLite DB; ensure messages align with expectations.
   - Risks: Overly verbose output; missing exception handling leading to silent failures.

2. **Stage 2: Add summary counts / skip indicators**
   - Dependencies: Stage 1 logging present.
   - Changes: Use SQLAlchemy inspector to compare existing tables versus metadata; report counts created vs already existing. Include timing if helpful.
   - Testing: Manual runs across databases with different states; unit test helper function if extracted.
   - Risks: Inspector differences across database backends; inaccurate counts if metadata drifts from actual schema.

3. **Stage 3: Warning/error surfacing**
   - Dependencies: Stages 1-2 installed.
   - Changes: Ensure exceptions during engine creation or table creation are caught, logged with context, and exit code set non-zero. Add warnings for partial completion when some tables fail.
   - Testing: Simulate failure (bad connection string) and confirm output + exit code; verify happy path unaffected.
   - Risks: Over-catching exceptions and masking stack traces; inconsistent exit statuses.

4. **Stage 4: QA + documentation**
   - Dependencies: Stages 1-3 complete.
   - Changes: Record implementation summary, update CLI documentation/readme snippet, note future enhancements (e.g., migration runner integration).
   - Testing: Final manual smoke test on empty/existing DB; update feature summary doc.
   - Risks: Forgetting to document new messaging; confusion if localization/log formatting differs per environment.
