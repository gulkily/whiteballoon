from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import SessionDep, SessionUser, require_session_user

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


@router.post("/ai", response_model=ChatAIResponse)
def chat_ai_query(
    payload: ChatAIRequestPayload,
    db: SessionDep,
    session_user: SessionUser = Depends(require_session_user),
) -> ChatAIResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI chat endpoint contract only. Implementation arrives in later stages.",
    )
