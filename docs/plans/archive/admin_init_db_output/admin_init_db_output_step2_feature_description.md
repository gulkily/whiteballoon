# Admin Init-DB Output — Step 2 Feature Description

## Problem
Admin users running `./wb init-db` only see a generic success message, making it unclear whether the command validated connectivity, created tables, or skipped work because everything already existed.

## User Stories
- As an admin, I want the init-db command to report each major step (connecting, creating tables, seeding defaults) so I know what happened.
- As an admin, I want to see whether tables were created or skipped so I can confirm schema readiness without digging into the database.
- As an admin, I want any warnings or errors surfaced in the output so I can resolve configuration issues quickly.

## Core Requirements
- Emit structured, human-friendly log lines for connection checks, metadata creation, and completion status.
- Indicate whether tables were newly created or already present (e.g., “created 5 tables”, “all tables already existed”).
- Surface warnings when the command cannot create tables or connect, exiting with non-zero status on failure.
- Keep output suitable for both interactive use and CI scripts (no interactive prompts).

## User Flow
1. Admin runs `./wb init-db`.
2. Script announces database connection target, creates engine, and validates connectivity.
3. Script reports table creation results and any seed/default steps.
4. Script exits with clear success message including counts and/or skips; errors include actionable context.

## Success Criteria
- Running the command against an empty database prints step-by-step updates and confirms tables were created.
- Running the command against an existing database reports that tables already exist without implying failure.
- Failures (e.g., bad connection string) produce clear error output and non-zero exit code.
- Output remains concise but informative, suitable for redirecting to logs.
