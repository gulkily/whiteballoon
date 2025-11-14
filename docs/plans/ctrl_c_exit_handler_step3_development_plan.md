# Ctrl-C Exit Handler — Development Plan

## Stage 1 – Understand current shutdown path
- **Goal**: Confirm how `./wb runserver` launches the dev server and where the `KeyboardInterrupt` bubbles up.
- **Dependencies**: None.
- **Changes**: Read `wb.py` around `dev_invoke`, `cmd_known`, and the `runserver` command implementation; note how signals propagate from the child process.
- **Verification**: Add notes (not code) confirming the call path and exit codes.
- **Risks**: Missing an unexpected code path (e.g., different commands) that also needs handling.

## Stage 2 – Implement graceful interrupt handling
- **Goal**: Prevent the traceback while retaining real error reporting.
- **Dependencies**: Stage 1 insights about the control flow.
- **Changes**: Wrap the subprocess invocation in `dev_invoke` (or the appropriate layer) with `try/except KeyboardInterrupt`, ensure the child gets SIGINT, suppress the stack trace, and exit 0 (possibly logging a concise "Server stopped" message). Keep behavior unchanged for non-interrupt errors.
- **Verification**: Run `./wb runserver`, send `Ctrl-C`, ensure only graceful shutdown logs appear and the exit code is 0. Spot-check another command (e.g., `./wb version`) to confirm errors still surface.
- **Risks**: Accidentally hiding other exceptions or swallowing non-interrupt failures.

## Stage 3 – Document and sanity check
- **Goal**: Capture the change and confirm repo cleanliness.
- **Dependencies**: Stage 2 implementation complete.
- **Changes**: Update any relevant developer documentation (if needed) to mention the clean shutdown behavior; ensure formatting/linting if applicable.
- **Verification**: Re-run `./wb runserver` interrupt test, confirm git status shows intended changes only or document additional ones.
- **Risks**: Forgetting to mention new behavior or missing side effects revealed during final smoke test.
