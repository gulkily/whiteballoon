from __future__ import annotations

import logging
from typing import Literal
from uuid import uuid4
from time import perf_counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import SessionDep, SessionUser, require_session_user
from app.services import chat_ai_metrics, chat_ai_service

CHAT_AI_RATE_LIMIT_PER_MINUTE = 30
CHAT_AI_MAX_HISTORY = 5


router = APIRouter(prefix="/api/chat", tags=["chat-ai"])


class ChatAIMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatAICitation(BaseModel):
    id: str = Field(..., description="Stable identifier of the referenced object (request/comment/etc).")
    label: str = Field(..., description="Short display label for the resource.")
    url: str | None = Field(default=None, description="Deep link to view the referenced data.")
    snippet: str | None = Field(default=None, description="Optional supporting snippet or context preview.")
    reaction_summary: list[dict[str, object]] | None = Field(
        default=None,
        description="Optional reaction counts derived from `(Reactions: …)` suffixes.",
    )
    source_type: Literal["request", "comment", "doc", "user", "other"] = "other"


class ChatAIRequestPayload(BaseModel):
    prompt: str = Field(..., min_length=1, description="User question in natural language.")
    conversation_id: str | None = Field(
        default=None,
        description="Opaque conversation identifier so the backend can load short-term context.",
    )
    context_scope: Literal["auto", "requests", "chats", "docs"] = Field(
        default="auto",
        description="Optional restriction for which corpus to search before generating the answer.",
    )
    max_context_items: int = Field(
        default=CHAT_AI_MAX_HISTORY,
        ge=1,
        le=10,
        description="Number of previous exchanges to retain for continuity. Capped to keep prompts bounded.",
    )


class ChatAIResponse(BaseModel):
    conversation_id: str
    messages: list[ChatAIMessage]
    citations: list[ChatAICitation] = Field(default_factory=list)
    guardrail_message: str | None = Field(
        default=None,
        description="Optional warning/guardrail text when the requested action cannot be completed.",
    )


_logger = logging.getLogger(__name__)


@router.post("/ai", response_model=ChatAIResponse)
def chat_ai_query(
    payload: ChatAIRequestPayload,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> ChatAIResponse:
    started = perf_counter()
    conversation_id = payload.conversation_id or uuid4().hex
    max_items = min(payload.max_context_items, CHAT_AI_MAX_HISTORY)
    context = chat_ai_service.build_ai_chat_context(
        db,
        prompt=payload.prompt,
        user=session_user.user,
        context_scope=payload.context_scope,
        max_items=max_items,
    )
    citations = [
        ChatAICitation(
            id=item.id,
            label=item.label,
            url=item.url,
            snippet=item.snippet,
            reaction_summary=item.reaction_summary or None,
            source_type=item.source_type if item.source_type in {"request", "comment", "doc", "user", "other"} else "other",
        )
        for item in context.citations
    ]
    assistant_reply = _compose_response_text(payload.prompt, context, citations)
    messages = [
        ChatAIMessage(role="user", content=payload.prompt),
        ChatAIMessage(role="assistant", content=assistant_reply),
    ]
    _logger.info(
        "chat-ai user=%s convo=%s citations=%s scope=%s",
        session_user.user.id,
        conversation_id,
        len(citations),
        payload.context_scope,
    )
    chat_ai_metrics.log_event(
        source="web",
        user_id=session_user.user.id,
        conversation_id=conversation_id,
        prompt=payload.prompt,
        citation_count=len(citations),
        status="guardrail" if context.guardrail else "ok",
        latency_ms=(perf_counter() - started) * 1000,
        guardrail=context.guardrail,
    )
    return ChatAIResponse(
        conversation_id=conversation_id,
        messages=messages,
        citations=citations,
        guardrail_message=context.guardrail,
    )


def _compose_response_text(
    prompt: str,
    context: chat_ai_service.ChatAIContextResult,
    citations: list[ChatAICitation],
) -> str:
    if not citations and context.guardrail:
        return context.guardrail
    if not citations:
        return "I couldn't find any matching requests or chat messages. Try adding specific keywords or request IDs."
    request_count = len(context.request_citations)
    comment_count = len(context.comment_citations)
    if request_count and comment_count:
        summary = (
            f"I found {request_count} request{'s' if request_count != 1 else ''} and "
            f"{comment_count} chat message{'s' if comment_count != 1 else ''} related to that."
        )
    elif request_count:
        summary = f"I found {request_count} request{'s' if request_count != 1 else ''} related to that."
    else:
        summary = f"I found {comment_count} chat message{'s' if comment_count != 1 else ''} related to that."

    response_parts = [summary, "See Sources for the full list."]
    if context.guardrail:
        response_parts.append(context.guardrail)
    return " ".join(response_parts).strip()
