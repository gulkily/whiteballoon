# `wb chat` Command Group — Step 2 Feature Description

## Problem
Chat/comment tooling (`wb chat-index`, `wb chat-embed`, `wb comment-llm`) clutters the CLI root and doesn’t clearly communicate that these commands are related. Operators have to scan the entire `wb --help` output or remember the exact spelling.

## User Stories
- As an operator, I can run `wb chat index …` to rebuild caches using a predictable namespace instead of remembering top-level command names.
- As an engineer, I can call `wb chat embed …` / `wb chat llm …` for embeddings or comment LLM tagging without scanning the help text.
- As a Windows user, I get the same grouped experience via `wb.bat chat …` so docs and scripts stay consistent.

## Core Requirements
- Introduce a `chat` Click group under `wb` with subcommands `index`, `embed`, and `llm` (`llm` can alias the existing comment LLM helper).
- Keep existing top-level commands working as aliases (possibly hidden) so scripts don’t break; log a deprecation note in help output.
- Ensure grouped commands inherit all existing options (`--request-id`, adapters, etc.).
- Update README / cheatsheet / CLI help to highlight the new grouped syntax.

## Shared Component Inventory
- `wb.py` (Click CLI) / `wb.bat`: implement the new group and route existing functionality.
- Tooling modules: `app/tools/request_chat_index.py`, `..._embeddings.py`, `comment_llm` — reused as-is.
- Docs: `README.md`, `DEV_CHEATSHEET.md` sections referencing chat tooling.

## User Flow
1. User runs `wb chat index --request-id 42`; the new group forwards to the existing chat indexing logic, prints current output.
2. `wb chat embed --request-id 42 --adapter local` builds embeddings as before.
3. `wb chat llm …` (or similar) handles comment-level tagging.
4. `wb --help` shows the `chat` group, and `wb chat --help` lists the subcommands.

## Success Criteria
- `wb chat index/embed/llm` execute with identical behavior to the previous top-level commands.
- Legacy entry points (`wb chat-index`, etc.) still work (with optional warning) to maintain backward compatibility.
- CLI help and documentation reference the new structure.
- Windows batch wrapper mirrors the grouped commands.
