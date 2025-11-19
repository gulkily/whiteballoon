"""High-level helpers to log Dedalus interactions without interrupting main flows."""
from __future__ import annotations

import inspect
import logging
import secrets
from functools import wraps
from typing import Any, Callable, Sequence

from app.dedalus import log_store
from app.dedalus.redaction import redact_text

logger = logging.getLogger(__name__)


def _safe_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return func(*args, **kwargs)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Failed logging Dedalus interaction")
        return None


def start_logged_run(
    *,
    user_id: str | None,
    entity_type: str | None,
    entity_id: str | None,
    model: str | None,
    prompt: str,
    context_hash: str | None = None,
) -> str:
    prompt_clean = redact_text(prompt) or prompt
    run_id = secrets.token_hex(16)
    _safe_call(
        log_store.log_run_start,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        model=model,
        prompt=prompt_clean,
        context_hash=context_hash,
        run_id=run_id,
    )
    return run_id


def finalize_logged_run(
    *,
    run_id: str,
    response: str | None,
    status: str,
    error: str | None = None,
    structured_label: str | None = None,
    structured_tools: list[str] | None = None,
) -> None:
    response_clean = redact_text(response) if response else response
    error_clean = redact_text(error) if error else error
    _safe_call(
        log_store.finalize_run,
        run_id=run_id,
        response=response_clean,
        status=status,
        error=error_clean,
        structured_label=structured_label,
        structured_tools=",".join(structured_tools) if structured_tools else None,
    )


def instrument_tools(tools: Sequence[Callable[..., Any]] | None, run_id: str) -> list[Callable[..., Any]]:
    if not tools:
        return []
    return [_wrap_tool_callable(tool, run_id) for tool in tools]


def _wrap_tool_callable(func: Callable[..., Any], run_id: str) -> Callable[..., Any]:
    name = getattr(func, "__name__", func.__class__.__name__)

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            _log_tool_event(run_id, name, kwargs)
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                _log_tool_event(run_id, name, kwargs, status="error", output=str(exc))
                raise
            _log_tool_event(run_id, name, kwargs, status="success", output=_stringify(result))
            return result

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        _log_tool_event(run_id, name, kwargs)
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            _log_tool_event(run_id, name, kwargs, status="error", output=str(exc))
            raise
        _log_tool_event(run_id, name, kwargs, status="success", output=_stringify(result))
        return result

    return sync_wrapper


def _stringify(value: Any) -> str:
    text = str(value)
    return redact_text(text) or text


def _log_tool_event(
    run_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    status: str | None = None,
    output: str | None = None,
) -> None:
    prepare_args = {key: str(value) for key, value in arguments.items()}
    _safe_call(
        log_store.append_tool_call,
        run_id=run_id,
        tool_name=tool_name,
        arguments=prepare_args,
        output=redact_text(output) if output else output,
        status=status,
    )


async def finalize_from_response(run_id: str, response: Any, **extra: Any) -> None:
    """Persist Dedalus runner outputs (handles streamed results)."""

    if response is None:
        finalize_logged_run(run_id=run_id, response=None, status="unknown", **extra)
        return
    final_output = getattr(response, "final_output", None)
    if final_output:
        finalize_logged_run(
            run_id=run_id,
            response=_stringify(final_output),
            status="success",
            **extra,
        )
        return
    outputs = getattr(response, "outputs", None)
    if outputs:
        summary = "\n".join(_stringify(item) for item in outputs)
        finalize_logged_run(run_id=run_id, response=summary, status="success", **extra)
        return
    finalize_logged_run(run_id=run_id, response=_stringify(response), status="success", **extra)
