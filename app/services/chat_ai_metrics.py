from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

LOG_PATH = Path("storage/logs/chat_ai_events.log")
OPT_OUT_MARKER = "#private"


def log_event(
    *,
    source: str,
    user_id: int | None,
    conversation_id: str | None,
    prompt: str,
    citation_count: int,
    status: str,
    latency_ms: float,
    guardrail: str | None = None,
) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    snapshot, opted_out = _prepare_prompt(prompt)
    payload: dict[str, Any] = {
        "ts_ms": int(time.time() * 1000),
        "source": source,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "prompt": snapshot,
        "opt_out": opted_out,
        "citations": citation_count,
        "status": status,
        "latency_ms": round(latency_ms, 2),
    }
    if guardrail:
        payload["guardrail"] = guardrail
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _prepare_prompt(prompt: str) -> tuple[str, bool]:
    normalized = (prompt or "").strip()
    lowered = normalized.lower()
    if OPT_OUT_MARKER in lowered:
        return "[redacted]", True
    truncated = normalized[:280]
    return truncated, False


__all__ = ["log_event", "OPT_OUT_MARKER"]
