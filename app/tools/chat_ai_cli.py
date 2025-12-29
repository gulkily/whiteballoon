from __future__ import annotations

import argparse
import sys
from typing import Iterable
from uuid import uuid4
from time import perf_counter

from sqlmodel import Session, select

from app.db import get_engine
from app.models import User
from app.services import chat_ai_metrics, chat_ai_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interactive AI chat helper for querying WhiteBalloon data.")
    parser.add_argument("--user", help="Username to impersonate (defaults to the first admin or earliest user).")
    parser.add_argument(
        "--scope",
        choices=["auto", "requests", "chats", "docs"],
        default="auto",
        help="Restrict retrieval to a corpus.",
    )
    parser.add_argument("--max-items", type=int, default=5, help="Maximum citations per corpus (default: 5).")
    parser.add_argument("--prompt", help="Optional single prompt to run non-interactively.")
    args = parser.parse_args(argv)

    engine = get_engine()
    with Session(engine) as session:
        user = _resolve_user(session, args.user)
        if not user:
            print("No matching user found. Use --user to pick a valid username.", file=sys.stderr)
            return 1

        conversation_id = uuid4().hex
        print(f"Impersonating @{user.username} (conversation {conversation_id}). Type 'exit' to leave.")

        if args.prompt:
            _handle_prompt(session, user, args.prompt, args.scope, args.max_items)
            return 0

        while True:
            try:
                prompt = input("You> ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if not prompt:
                continue
            lowered = prompt.lower()
            if lowered in {"exit", "quit"}:
                break
            _handle_prompt(session, user, prompt, args.scope, args.max_items)
    return 0


def _resolve_user(session: Session, username: str | None) -> User | None:
    stmt = select(User)
    if username:
        stmt = stmt.where(User.username == username)
    else:
        stmt = stmt.order_by(User.is_admin.desc(), User.id.asc())
    return session.exec(stmt).first()


def _handle_prompt(session: Session, user: User, prompt: str, scope: str, max_items: int) -> None:
    started = perf_counter()
    context = chat_ai_service.build_ai_chat_context(
        session,
        prompt=prompt,
        user=user,
        context_scope=scope,
        max_items=max_items,
    )
    latency_ms = (perf_counter() - started) * 1000
    response = _format_response(context)
    print(f"AI> {response}")
    _print_citations(context.citations)
    chat_ai_metrics.log_event(
        source="cli",
        user_id=user.id,
        conversation_id=None,
        prompt=prompt,
        citation_count=len(context.citations),
        status="guardrail" if context.guardrail else "ok",
        latency_ms=latency_ms,
        guardrail=context.guardrail,
    )


def _format_response(context: chat_ai_service.ChatAIContextResult) -> str:
    if context.guardrail and context.is_empty():
        return context.guardrail
    lines: list[str] = []
    if context.request_citations:
        lines.append("Requests:")
        for idx, citation in enumerate(context.request_citations, start=1):
            lines.append(f"  {idx}. {citation.label} — {citation.snippet}")
    if context.comment_citations:
        lines.append("Comments:")
        for idx, citation in enumerate(context.comment_citations, start=1):
            lines.append(f"  {idx}. {citation.label} — {citation.snippet}")
    if not lines:
        lines.append("No matching requests or chats found. Try refining your question.")
    if context.guardrail:
        lines.append(context.guardrail)
    return "\n".join(lines)


def _print_citations(citations: Iterable[chat_ai_service.ChatAIContextCitation]) -> None:
    items = list(citations)
    if not items:
        return
    print("Sources:")
    for idx, citation in enumerate(items, start=1):
        print(f"  [{idx}] {citation.label} -> {citation.url}")


if __name__ == "__main__":
    raise SystemExit(main())
