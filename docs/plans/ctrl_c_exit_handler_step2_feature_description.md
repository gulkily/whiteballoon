# Ctrl-C Exit Handler — Feature Description

## Problem
When the local operator stops the dev server with `Ctrl-C`, the parent `./wb runserver` command prints a long Python `KeyboardInterrupt` traceback, creating noisy logs and implying an error even though shutdown completed normally.

## User Stories
- As a local operator, I want the CLI to exit cleanly after pressing `Ctrl-C` so I can trust that nothing failed during shutdown.
- As a developer, I want graceful signal handling in the `wb` launcher so the terminal output stays readable during frequent restarts.
- As a teammate reviewing logs, I want to see a concise "server stopped" message instead of a traceback so I can spot real failures quickly.

## Core Requirements
- Suppress the `KeyboardInterrupt` traceback emitted by the parent `wb` process when the child server exits due to `Ctrl-C`.
- Preserve FastAPI/Uvicorn’s existing graceful shutdown logs ("Shutting down", etc.).
- Ensure the `wb` command exits with a zero status when shutdown was operator-initiated.

## User Flow
1. Operator runs `./wb runserver` to start the dev server.
2. Operator presses `Ctrl-C` to stop the server.
3. Uvicorn performs its normal graceful shutdown and logs completion.
4. The `wb` launcher detects the interrupt/exit condition, suppresses the traceback, and prints a short confirmation (e.g., "Server stopped").
5. The CLI returns to the shell prompt without extra stack traces.

## Success Criteria
- Reproducing the previous scenario no longer prints a Python traceback after `Ctrl-C`.
- `./wb runserver` exits with status code 0 after operator-initiated shutdown.
- No regression in other `wb` subcommands; they still surface real errors.
