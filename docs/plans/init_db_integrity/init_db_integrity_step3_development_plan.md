# Init DB Integrity — Step 3 Development Plan

1. **Stage 1: Schema inspector helper**
   - Dependencies: SQLAlchemy inspector and SQLModel metadata.
   - Changes: Create utility to map metadata tables/columns and compare against live schema (names, types, nullability where possible).
   - Testing: Unit tests for helper using in-memory SQLite; manual run with existing DB.
   - Risks: Type comparison across dialects; limited constraint visibility without Alembic.

2. **Stage 2: Auto-repair for missing tables/columns**
   - Dependencies: Stage 1 difference detection.
   - Changes: For missing tables, reuse `SQLModel.metadata.tables[name].create(engine, checkfirst=False)`; for missing columns, issue `ALTER TABLE ADD COLUMN` using SQLModel metadata.
   - Testing: Manual scenario removing column/table and verifying repair; unit tests if feasible.
   - Risks: Alter column operations not supported; cannot change types safely.

3. **Stage 3: Integrate with `init-db` command**
   - Dependencies: Stage 2 logic.
   - Changes: Enhance `tools/dev.py:init_db_command` to run the inspector, apply repairs, and collect results before/after existing summary output.
   - Testing: Manual CLI run on clean + drifted DBs; ensure exit codes reflect unrepaired errors.
   - Risks: Command output clutter; catching exceptions without hiding context.

4. **Stage 4: Reporting and documentation**
   - Dependencies: Stage 3 integration.
   - Changes: Format summary (counts of fixes, outstanding warnings); update README/docs describing integrity check; mention new behavior in DEV_CHEATSHEET.
   - Testing: Manual doc review.
   - Risks: Forgetting to update docs; summary text too verbose.

5. **Stage 5: QA**
   - Dependencies: Stages 1-4 complete.
   - Changes: Run `pytest` (even if empty) and manual CLI tests; document results in Step 4 summary.
   - Risks: Missing edge cases; database backups recommended before auto-fix.
