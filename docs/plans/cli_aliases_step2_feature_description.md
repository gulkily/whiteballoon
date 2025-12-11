# CLI Aliases for Comment/Chat Commands — Step 2 Feature Description

## Problem
The existing `wb` CLI exposes verbose subcommands for comment/chat maintenance (`./wb comment-llm`, `./wb chat-index`, `./wb chat-embed`). Ops and developers keep mistyping or forgetting the exact entry points, slowing down workflows when they need to quickly reindex chats or regenerate comment LLM metadata.

## User Stories
- As an operator, I can type `wb chat-index --request-id 123` instead of remembering `./wb chat-index`, so I can refresh caches with muscle memory.
- As a developer, I can run `wb comment-llm --request-id 456 --adapter dedalus` without digging through docs to recall the script name.
- As a Windows user, I can use matching aliases via `wb.bat` without setting up custom shell aliases.

## Core Requirements
- Introduce friendly alias commands (`wb chat-index`, `wb chat-embed`, `wb comment-llm`) within the existing Click/Batch entry points that simply forward to the current implementations.
- Ensure aliases appear in `wb --help` output with concise descriptions so users discover them organically.
- Keep behavior identical to the original commands (all flags/options pass through unchanged) so scripts/docs don’t break.
- Update README / cheatsheet if necessary to reference the shorter forms.

## Shared Component Inventory
- `wb.py` (Click CLI entry point) and `wb.bat`: will host the alias wiring.
- Existing tooling modules (`app/tools/request_chat_index.py`, `app/tools/request_chat_embeddings.py`, `app/tools/comment_llm.py`) are reused; no code changes expected there.
- Docs: `README.md`, `DEV_CHEATSHEET.md` mention the commands and should highlight the aliases.

## User Flow
1. User runs `wb chat-index --request-id 42` (or corresponding options); the alias forwards to the existing chat index command and prints the same output as before.
2. Similarly, `wb chat-embed` and `wb comment-llm` act as shorthand for their respective tools.
3. Help output and docs show the aliases so new operators pick them up quickly.

## Success Criteria
- Running `wb chat-index`, `wb chat-embed`, and `wb comment-llm` executes successfully with all standard options.
- `wb --help` (and `wb chat-index --help`, etc.) show the alias descriptions.
- README / cheatsheet references the short commands.
- No behavior change for existing scripts that still use the long form.
