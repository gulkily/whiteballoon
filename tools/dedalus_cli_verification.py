#!/usr/bin/env python3
"""Option A POC: use Dedalus to drive an existing WhiteBalloon CLI workflow."""
from __future__ import annotations

import argparse
import asyncio
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

LOG_PREFIX = "[dedalus-cli]"


def _pre_boot_interrupt(signum, frame) -> None:  # pragma: no cover - signal handler
    print(f"{LOG_PREFIX} Interrupted before startup; exiting", flush=True)
    raise SystemExit(0)


signal.signal(signal.SIGINT, _pre_boot_interrupt)

from app.env import ensure_env_loaded

try:  # pragma: no cover - optional dependency check
    from dedalus_labs import AsyncDedalus, DedalusRunner
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise SystemExit(
        "Missing 'dedalus-labs' SDK. Run './wb setup' or 'pip install dedalus-labs' inside the venv."
    ) from exc

REPO_ROOT = Path(__file__).resolve().parent.parent
WB_SCRIPT = REPO_ROOT / "wb.py"

# Global knobs tweaked by CLI args so the tool reflects the requested scope.
TOOL_DEFAULT_LIMIT = 5
TOOL_INCLUDE_PROCESSED = False


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}")


def _run_wb_command(args: list[str]) -> str:
    """Execute wb.py with the provided args and return combined stdout/stderr."""

    cmd = [sys.executable, str(WB_SCRIPT), *args]
    display = " ".join(shlex.quote(part) for part in ["wb", *args])
    log(f"Invoking CLI: {display}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode != 0:
        details = stderr or stdout or "command produced no output"
        log(f"CLI exited with {proc.returncode}; propagating failure")
        raise RuntimeError(f"Command 'wb {' '.join(args)}' exited {proc.returncode}: {details}")
    log(
        "CLI finished successfully (stdout lines: {stdout_lines}, stderr lines: {stderr_lines})".format(
            stdout_lines=len(stdout.splitlines()) if stdout else 0,
            stderr_lines=len(stderr.splitlines()) if stderr else 0,
        )
    )
    if stdout:
        log("CLI stdout:\n" + stdout)
    if stderr:
        log("CLI stderr:\n" + stderr)
    if not stdout and not stderr:
        return "(command produced no output)"
    parts: list[str] = []
    if stdout:
        parts.append(stdout)
    if stderr:
        parts.append(f"[stderr]\n{stderr}")
    return "\n\n".join(parts)


def audit_auth_requests(limit: Optional[int] = None, include_processed: Optional[bool] = None) -> str:
    """Run the 'wb session list' CLI to audit authentication requests."""

    effective_limit = limit if limit not in (None, 0) else TOOL_DEFAULT_LIMIT
    effective_include = TOOL_INCLUDE_PROCESSED if include_processed is None else include_processed

    wb_args = ["session", "list"]
    if effective_include:
        wb_args.append("--all")
    if effective_limit and effective_limit > 0:
        wb_args.extend(["--limit", str(effective_limit)])

    return _run_wb_command(wb_args)


def _build_prompt(limit: int, include_processed: bool) -> str:
    scope = "pending authentication requests only"
    if include_processed:
        scope = "all authentication requests, including processed ones"
    return (
        "Use the `audit_auth_requests` tool to run the real WhiteBalloon CLI. "
        f"Capture {scope} with a limit of {limit} rows, then summarize what you see. "
        "Provide two sections in your final response: a bullet summary and the CLI output inside a fenced code block tagged as text."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Dedalus Option A proof-of-concept that calls the wb session audit CLI via MCP tools."
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Dedalus model alias to use (default: openai/gpt-5-mini or DEDALUS_POC_MODEL env)",
    )
    parser.add_argument("--limit", type=int, default=5, help="Rows to request from the wb session list command")
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="Show processed/closed authentication requests instead of pending only",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Override the default instructions sent to Dedalus (advanced)",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    log("Loading environment variables from .env")
    ensure_env_loaded()
    api_key = os.getenv("DEDALUS_API_KEY")
    if not api_key:
        print("Set DEDALUS_API_KEY in your .env before running this script.", file=sys.stderr)
        return 1

    global TOOL_DEFAULT_LIMIT, TOOL_INCLUDE_PROCESSED
    TOOL_DEFAULT_LIMIT = max(1, args.limit)
    TOOL_INCLUDE_PROCESSED = args.include_processed
    log(
        f"Configured tool scope → limit={TOOL_DEFAULT_LIMIT}, include_processed={TOOL_INCLUDE_PROCESSED}"
    )

    instructions = args.prompt or _build_prompt(TOOL_DEFAULT_LIMIT, TOOL_INCLUDE_PROCESSED)
    model = args.model or os.getenv("DEDALUS_POC_MODEL") or "openai/gpt-5-mini"
    log(f"Using Dedalus model: {model}")

    try:
        client = AsyncDedalus()
    except TypeError:  # pragma: no cover - backwards compatibility when api_key required
        client = AsyncDedalus(api_key=api_key)
    runner = DedalusRunner(client)

    log("Starting Dedalus runner invocation")
    try:
        response = await runner.run(
            input=instructions,
            model=model,
            tools=[audit_auth_requests],
        )
    except Exception as exc:  # pragma: no cover - external dependency
        print(f"Dedalus request failed: {exc}", file=sys.stderr)
        return 1
    log("Dedalus runner finished; streaming final output")

    output = getattr(response, "final_output", None)
    if not output:
        outputs = getattr(response, "outputs", None)
        if isinstance(outputs, list) and outputs:
            output = "\n".join(str(item) for item in outputs)
        else:
            output = str(response)
    print(output)
    return 0


def main() -> None:
    args = _parse_args()
    log("Dedalus CLI verification bootstrap starting")
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        exit_code = asyncio.run(run(args))
    except KeyboardInterrupt:
        log("Interrupted by Ctrl-C; stopping Dedalus verification")
        exit_code = 0
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
