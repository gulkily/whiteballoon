# Init DB Integrity — Step 2 Feature Description

## Problem
`./wb init-db` only creates missing tables; it doesn’t confirm existing tables match the SQLModel schema, so admins can’t rely on it to detect or repair structural drift.

## User Stories
- As an admin, I want `init-db` to confirm the live database schema matches the model definitions so I can trust the environment before development or deployment.
- As an admin, I want the command to repair simple discrepancies (missing columns/tables) automatically and summarize what changed.
- As a maintainer, I want a detailed report of detected schema issues even if full auto-fix isn’t possible so I can take further action.

## Core Requirements
- Inspect each table defined in SQLModel metadata, comparing with the live database schema (columns, types, constraints where feasible).
- Automatically create missing tables and columns when possible (non-destructive operations only).
- For mismatched column types or constraints that can’t be auto-fixed safely, emit warnings with actionable instructions.
- Provide a final report summarizing checks, repairs applied, and outstanding issues.
- Preserve the prior behavior of announcing connection info and table counts.

## User Flow
1. Admin runs `./wb init-db`.
2. Command connects to the database and prints initial status (URL, existing tables, etc.).
3. For each table, metadata is compared with live schema; any drift is fixed if safe or logged otherwise.
4. Summary report details results (e.g., “added column X”, “table Y up-to-date”, “warning: type mismatch on column Z”).
5. Command exits with non-zero status if unrepaired errors remain.

## Success Criteria
- Running `init-db` on an up-to-date schema reports “no changes needed”.
- Removing a column manually and re-running results in the column being recreated or warnings if not safe to alter.
- Summary output lists checks and actions clearly, enabling auditing.
- Documentation and CLI help reflect the new integrity-check functionality.
