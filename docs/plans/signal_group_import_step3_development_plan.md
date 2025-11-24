# Signal Group Import – Step 3 Development Plan

## Stage 1 – Export handoff workflow docs
- **Goal**: Document the exact Windows → WSL export workflow so developers know how to place the Signal Desktop export where the importer expects it.
- **Dependencies**: None.
- **Changes**: Add a short guide (e.g., `docs/dev/signal_group_export.md`) showing the Windows export steps, sample folder naming, and WSL path reference; mention permissions on `/mnt/c` to avoid read errors.
- **Verification**: Manually walk through an export on Windows, confirm the files are visible from WSL via `ls /mnt/c/...`.
- **Risks**: Missing prerequisite (being logged into the group) or forgetting to mention that only the target group should be exported.

## Stage 2 – CLI plumbing in `wb`
- **Goal**: Provide a `wb import-signal-group` subcommand wired into the existing CLI harness.
- **Dependencies**: Stage 1 documentation (paths referenced here).
- **Changes**: Update `wb.py` argparser to add `import-signal-group`; delegate to a new function (e.g., `cmd_import_signal_group`) in a module such as `app/tools/signal_import.py`; ensure poetry entry point works on Windows + WSL.
- **Verification**: Run `poetry run wb import-signal-group --help` to see help text and argument parsing succeed.
- **Risks**: Colliding with existing subcommand names; forgetting to load env before DB access.

## Stage 3 – Export parsing utility
- **Goal**: Read the Signal Desktop export (`.zip` or folder) and produce normalized Python objects for metadata, members, and messages.
- **Dependencies**: Stage 2 (CLI skeleton) to call the parser.
- **Changes**: Implement a parser module that can accept a folder path, unzip if needed, ingest `messages.json`, and expose iterables of messages (timestamp, sender, body, attachments). Normalize phone numbers/email IDs and capture the export’s “group id/address”.
- **Verification**: Unit-style test using a trimmed sample export placed under `tests/fixtures/signal_group_export`; running the parser should log counts and show correctly decoded messages.
- **Risks**: Signal export structure changes; large attachments causing high memory usage.

## Stage 4 – Contact and member mapping
- **Goal**: Resolve Signal participants to local `User` (or profile) records, creating placeholder records when needed.
- **Dependencies**: Stage 3 data structures.
- **Changes**: Add mapping logic that attempts to match by phone/email; when no match exists, create lightweight placeholder rows tagged with `source='signal_group_seed'` and store Signal nickname/number for later reconciliation.
- **Verification**: Manual DB check (e.g., `sqlitebrowser` or SQL query) ensuring duplicates are not created on repeated imports; CLI output summarizing new vs existing members.
- **Risks**: Overwriting real user data; race conditions if importer runs twice concurrently (mitigate with unique constraints/idempotent upserts).

## Stage 5 – Message + attachment import
- **Goal**: Insert the parsed messages/attachments into local tables so they appear in feeds/tests.
- **Dependencies**: Stage 4 member IDs.
- **Changes**: Create or reuse models for messages/resources; insert rows with timestamps, text, attachment metadata, and `source_group_id`. Ensure the importer tracks a checksum or message GUID to skip duplicates on reruns.
- **Verification**: Run importer against sample export, then query `requests`/`messages` tables to confirm counts; ensure feed UI shows entries tagged with the new source label.
- **Risks**: Schema mismatches, missing migrations, or large exports slowing down inserts (use bulk operations where possible).

## Stage 6 – Logging, idempotency, and cleanup
- **Goal**: Produce a local log file and ensure reruns are safe.
- **Dependencies**: Stages 2–5 complete.
- **Changes**: Write `signal_group_import.log` alongside the export containing counts/errors; add a summary printed to stdout. Store last-import timestamp per group (e.g., in a `signal_import_runs` table) so repeated executions either upsert or no-op cleanly. Document verification steps in the Step 4 summary template.
- **Verification**: Run importer twice with same export; confirm log updates, no duplicate DB rows, and idempotency metadata reflects rerun.
- **Risks**: Log file path collisions or leaking sensitive data beyond local disk; missing error handling causing silent failures.
