# `wb chat` Command Group — Step 3 Development Plan

## Stage 1 – CLI wiring (`wb.py` / `wb.bat`)
- **Goal**: Introduce the `chat` Click group and move existing subcommands under it.
- **Changes**: In `wb.py`, define `@cli.group('chat')` and register `index`, `embed`, and `llm` subcommands that call the existing tooling functions. Update `wb.bat` to route `chat ...` arguments similarly. Ensure `wb chat --help` lists the subcommands.
- **Verification**: Run `wb chat --help`, `wb chat index --help`, etc., to confirm wiring without executing the tools.
- **Risks**: Typos or missing imports break CLI entry point; double-check batch script quoting on Windows.

## Stage 2 – Legacy aliases & help text
- **Goal**: Keep top-level commands functioning via aliases/deprecations.
- **Changes**: Define no-op wrappers (e.g., `@cli.command('chat-index')`) that forward to the grouped handlers and optionally print a deprecation notice. Update `wb --help` to highlight the `chat` group and mention the short names in README/cheatsheet.
- **Verification**: Run both `wb chat index ...` and `wb chat-index ...` to confirm identical behavior.
- **Risks**: Forgetting to sync doc references or leaving stale instructions.

## Stage 3 – Documentation updates
- **Goal**: Reflect the new structure in user docs.
- **Changes**: Update `README.md` and `DEV_CHEATSHEET.md` to reference `wb chat index/embed/llm` as the canonical commands (mention legacy names once).
- **Verification**: Proofread docs and ensure examples match actual CLI.
- **Risks**: Documentation drift; ensure instructions align with code.

## Stage 4 – Smoke test commands
- **Goal**: Validate that each subcommand still executes end-to-end.
- **Changes**: Run representative commands (e.g., `wb chat index --request-id 1 --dry-run`, `wb chat embed --request-id 1 --adapter local`, `wb chat llm --help`) and confirm outputs. No code edits other than verifying.
- **Verification**: Manual CLI runs.
- **Risks**: None (manual testing step).
