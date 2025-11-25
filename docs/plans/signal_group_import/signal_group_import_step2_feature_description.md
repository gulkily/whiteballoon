# Signal Group Import – Step 2 Feature Description

## Problem
Developers need a reliable way to import one specific Signal group chat into the local whiteballoon instance (Windows host running WSL) so that early database and feature work can use realistic data before general Signal integration ships.

## User Stories
- As a developer, I want to export the targeted Signal group from Windows Signal Desktop and drop it into a shared folder so WSL tooling can access the raw JSON/attachments.
- As a backend engineer, I want a CLI importer that converts the export into normalized records (members, messages, attachments) in my local database so I can test request feeds.
- As a privacy reviewer, I want the import process to keep all data local to my machine and clearly log what was ingested so nothing leaks outside development.

## Core Requirements
- Provide a documented Windows+WSL workflow for exporting the chosen Signal group and making the `.zip`/`.json` artifacts available under `/mnt/c/...`.
- Build an importer command (e.g., `poetry run wb import-signal-group --export-path ... --group-id ...`) that parses the export, maps contacts to existing local users (creating placeholders as needed), and inserts messages into the database.
- Tag imported data so it is distinguishable (e.g., `source='signal_group_seed'`) and can be re-imported idempotently when a new export arrives.
- Store a plaintext import log summarizing counts of members, messages, and attachments processed.

## User Flow
1. User opens Signal Desktop on Windows, exports the target group (`Settings → Chats → Export`), and saves it to `C:\Users\<user>\Documents\signal_exports`.
2. User opens WSL and ensures the export is accessible at `/mnt/c/Users/<user>/Documents/signal_exports/<timestamped-folder>`.
3. User runs `poetry run wb import-signal-group --export-path /mnt/c/... --group-id <group-address>` inside WSL.
4. Importer parses the export, normalizes members/messages, writes them into the local DB, and prints log output plus a `signal_group_import.log` file.
5. Developer verifies seeded data via existing CLI/UI flows.

## Success Criteria
- Importer completes without manual SQL steps and reports success in both stdout and the log file.
- Running the importer twice with the same export does not duplicate members or messages.
- Imported messages appear in the local feed or database queries as expected, scoped to the single group chat.
- No network calls or data syncing outside the developer machine during the workflow.
