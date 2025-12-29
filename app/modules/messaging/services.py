from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from sqlmodel import Session, select

from app.modules.messaging.db import get_messaging_session
from app.modules.messaging.models import Message, MessageParticipant, MessageThread


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_direct_key(user_a_id: int, user_b_id: int) -> str:
    low, high = sorted((int(user_a_id), int(user_b_id)))
    return f"{low}:{high}"


def _ensure_direct_thread(session: Session, user_id: int, target_user_id: int) -> MessageThread:
    direct_key = build_direct_key(user_id, target_user_id)
    statement = select(MessageThread).where(MessageThread.direct_key == direct_key)
    thread = session.exec(statement).first()
    if thread:
        return thread

    now = _now()
    thread = MessageThread(
        created_by_user_id=user_id,
        direct_key=direct_key,
        created_at=now,
        updated_at=now,
        latest_message_at=now,
    )
    session.add(thread)
    session.flush()
    participants = [
        MessageParticipant(
            thread_id=thread.id,
            user_id=user_id,
            joined_at=now,
            last_read_at=now,
            unread_count=0,
        ),
        MessageParticipant(
            thread_id=thread.id,
            user_id=target_user_id,
            joined_at=now,
            unread_count=0,
        ),
    ]
    for participant in participants:
        session.add(participant)
    return thread


def ensure_direct_thread(user_id: int, target_user_id: int) -> MessageThread:
    with get_messaging_session() as session:
        thread = _ensure_direct_thread(session, user_id, target_user_id)
        session.commit()
        session.refresh(thread)
        return thread


def _load_participants(session: Session, thread_id: int) -> list[MessageParticipant]:
    statement = select(MessageParticipant).where(MessageParticipant.thread_id == thread_id)
    return list(session.exec(statement))


def send_direct_message(sender_id: int, recipient_id: int, body: str) -> tuple[Message, MessageThread]:
    payload = (body or "").strip()
    if not payload:
        raise ValueError("Message body required")
    with get_messaging_session() as session:
        thread = _ensure_direct_thread(session, sender_id, recipient_id)
        message = Message(thread_id=thread.id, sender_user_id=sender_id, body=payload)
        session.add(message)
        session.flush()
        participants = _load_participants(session, thread.id)
        for participant in participants:
            if participant.user_id == sender_id:
                participant.last_read_at = message.created_at
                participant.unread_count = 0
                session.add(participant)
            else:
                participant.unread_count = (participant.unread_count or 0) + 1
                session.add(participant)
        thread.latest_message_at = message.created_at
        thread.updated_at = message.created_at
        session.add(thread)
        session.commit()
        session.refresh(message)
        session.refresh(thread)
        return message, thread


@dataclass
class ThreadSummary:
    thread: MessageThread
    participants: list[MessageParticipant]
    last_message: Message | None


@dataclass
class ThreadDetail:
    thread: MessageThread
    participants: list[MessageParticipant]
    messages: list[Message]
    viewer_participant: MessageParticipant


def list_threads_for_user(user_id: int, limit: int = 50) -> list[ThreadSummary]:
    with get_messaging_session() as session:
        statement = (
            select(MessageThread)
            .join(MessageParticipant)
            .where(MessageParticipant.user_id == user_id)
            .order_by(MessageThread.latest_message_at.desc())
            .limit(limit)
        )
        threads = list(session.exec(statement))
        if not threads:
            return []
        thread_ids = [thread.id for thread in threads if thread.id is not None]
        participant_rows = session.exec(
            select(MessageParticipant).where(MessageParticipant.thread_id.in_(thread_ids))
        ).all()
        participant_map: dict[int, list[MessageParticipant]] = {}
        for participant in participant_rows:
            participant_map.setdefault(participant.thread_id, []).append(participant)
        summaries: list[ThreadSummary] = []
        for thread in threads:
            last_message = session.exec(
                select(Message)
                .where(Message.thread_id == thread.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            ).first()
            summaries.append(
                ThreadSummary(
                    thread=thread,
                    participants=participant_map.get(thread.id, []),
                    last_message=last_message,
                )
            )
        return summaries


def load_thread_for_user(user_id: int, thread_id: int) -> ThreadDetail | None:
    with get_messaging_session() as session:
        viewer_participant = session.exec(
            select(MessageParticipant)
            .where(MessageParticipant.thread_id == thread_id)
            .where(MessageParticipant.user_id == user_id)
        ).first()
        if not viewer_participant:
            return None
        thread = session.get(MessageThread, thread_id)
        if not thread:
            return None
        participants = _load_participants(session, thread_id)
        messages = session.exec(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.asc())
        ).all()
        return ThreadDetail(
            thread=thread,
            participants=participants,
            messages=messages,
            viewer_participant=viewer_participant,
        )


def mark_thread_read(user_id: int, thread_id: int) -> bool:
    with get_messaging_session() as session:
        participant = session.exec(
            select(MessageParticipant)
            .where(MessageParticipant.thread_id == thread_id)
            .where(MessageParticipant.user_id == user_id)
        ).first()
        if not participant:
            return False
        participant.last_read_at = _now()
        participant.unread_count = 0
        session.add(participant)
        session.commit()
        return True


__all__ = [
    "ThreadDetail",
    "ThreadSummary",
    "build_direct_key",
    "ensure_direct_thread",
    "list_threads_for_user",
    "load_thread_for_user",
    "mark_thread_read",
    "send_direct_message",
]
