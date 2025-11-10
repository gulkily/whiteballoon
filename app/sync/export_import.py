from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from sqlmodel import Session, select

from app.config import get_settings
from app.models import (
    HelpRequest,
    InvitePersonalization,
    InviteToken,
    RequestComment,
    User,
)
from app.services.request_comment_service import serialize_comment

SCHEMA_VERSION = "1"


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() + "Z" if dt else None


def _write_sync_file(path: Path, headers: dict[str, str], body: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for key, value in headers.items():
            fh.write(f"{key}: {value}\n")
        fh.write("\n")
        fh.write(json.dumps(body, indent=2, sort_keys=True))
        fh.write("\n")


def export_sync_data(session: Session, output_dir: Path) -> list[Path]:
    if output_dir.exists():
        for existing in output_dir.rglob("*.sync.txt"):
            existing.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    instance_id = settings.site_url or "local-instance"
    exported: list[Path] = []

    # Users
    users = session.exec(select(User).where(User.sync_scope == "public")).all()
    for user in users:
        body = {
            "id": user.id,
            "username": user.username,
            "contact_email": user.contact_email,
            "created_at": _iso(user.created_at),
            "sync_scope": user.sync_scope,
        }
        headers = {
            "Entity": "user",
            "ID": str(user.id),
            "Instance": instance_id,
            "Schema-Version": SCHEMA_VERSION,
            "Updated-At": _iso(user.created_at) or "",
            "Sync-Scope": user.sync_scope,
        }
        path = output_dir / "users" / f"user_{user.id}.sync.txt"
        _write_sync_file(path, headers, body)
        exported.append(path)

    # Requests + comments
    requests = session.exec(select(HelpRequest).where(HelpRequest.sync_scope == "public")).all()
    request_ids = [req.id for req in requests]
    comments_map: dict[int, list[dict[str, object]]] = {req_id: [] for req_id in request_ids}
    if request_ids:
        rows = session.exec(
            select(RequestComment, User)
            .join(User, User.id == RequestComment.user_id)
            .where(RequestComment.help_request_id.in_(request_ids))
            .where(RequestComment.sync_scope == "public")
        ).all()
        for comment, author in rows:
            payload = serialize_comment(comment, author)
            comments_map.setdefault(comment.help_request_id, []).append(payload)

    for request_obj in requests:
        body = {
            "id": request_obj.id,
            "title": request_obj.title,
            "description": request_obj.description,
            "status": request_obj.status,
            "contact_email": request_obj.contact_email,
            "created_by_user_id": request_obj.created_by_user_id,
            "created_at": _iso(request_obj.created_at),
            "updated_at": _iso(request_obj.updated_at),
            "completed_at": _iso(request_obj.completed_at),
            "sync_scope": request_obj.sync_scope,
            "comments": comments_map.get(request_obj.id, []),
        }
        headers = {
            "Entity": "request",
            "ID": str(request_obj.id),
            "Instance": instance_id,
            "Schema-Version": SCHEMA_VERSION,
            "Updated-At": _iso(request_obj.updated_at) or "",
            "Sync-Scope": request_obj.sync_scope,
        }
        path = output_dir / "requests" / f"request_{request_obj.id}.sync.txt"
        _write_sync_file(path, headers, body)
        exported.append(path)

    # Invites
    invites = session.exec(select(InviteToken).where(InviteToken.sync_scope == "public")).all()
    personalization_rows = session.exec(select(InvitePersonalization)).all()
    personalization_by_token = {row.token: row for row in personalization_rows}

    for invite in invites:
        personalization = personalization_by_token.get(invite.token)
        body = {
            "token": invite.token,
            "created_by_user_id": invite.created_by_user_id,
            "created_at": _iso(invite.created_at),
            "expires_at": _iso(invite.expires_at),
            "max_uses": invite.max_uses,
            "use_count": invite.use_count,
            "auto_approve": invite.auto_approve,
            "suggested_username": invite.suggested_username,
            "suggested_bio": invite.suggested_bio,
            "sync_scope": invite.sync_scope,
            "personalization": None,
        }
        if personalization:
            body["personalization"] = {
                "photo_url": personalization.photo_url,
                "gratitude_note": personalization.gratitude_note,
                "support_message": personalization.support_message,
                "help_examples": personalization.help_examples,
                "fun_details": personalization.fun_details,
                "created_at": _iso(personalization.created_at),
            }
        headers = {
            "Entity": "invite",
            "ID": invite.token,
            "Instance": instance_id,
            "Schema-Version": SCHEMA_VERSION,
            "Updated-At": _iso(invite.created_at) or "",
            "Sync-Scope": invite.sync_scope,
        }
        path = output_dir / "invites" / f"invite_{invite.token}.sync.txt"
        _write_sync_file(path, headers, body)
        exported.append(path)

    # Manifest
    manifest_path = output_dir / "manifest.sync.txt"
    lines: list[str] = []
    for path in sorted(exported):
        rel = path.relative_to(output_dir)
        digest = sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel.as_posix()}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    exported.append(manifest_path)

    return exported


def _parse_sync_file(path: Path) -> tuple[dict[str, str], dict[str, object]]:
    headers: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                break
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        body_text = fh.read()
    body = json.loads(body_text or "{}")
    return headers, body


def import_sync_data(session: Session, input_dir: Path) -> int:
    if not input_dir.exists():
        raise FileNotFoundError(f"Sync directory not found: {input_dir}")
    count = 0
    files = sorted(p for p in input_dir.rglob("*.sync.txt") if p.name != "manifest.sync.txt")
    for path in files:
        headers, body = _parse_sync_file(path)
        entity = headers.get("Entity")
        if entity == "user":
            _import_user(session, body)
        elif entity == "request":
            _import_request(session, body)
        elif entity == "invite":
            _import_invite(session, body)
        count += 1
    session.commit()
    return count


def _import_user(session: Session, body: dict[str, object]) -> None:
    created_at = _parse_datetime(body.get("created_at"))
    user = User(
        id=body.get("id"),
        username=body.get("username"),
        contact_email=body.get("contact_email"),
        created_at=created_at or datetime.utcnow(),
        sync_scope=body.get("sync_scope", "public"),
    )
    session.merge(user)


def _import_request(session: Session, body: dict[str, object]) -> None:
    created_at = _parse_datetime(body.get("created_at"))
    updated_at = _parse_datetime(body.get("updated_at"))
    completed_at = _parse_datetime(body.get("completed_at"))
    request_obj = HelpRequest(
        id=body.get("id"),
        title=body.get("title"),
        description=body.get("description", ""),
        status=body.get("status", "open"),
        contact_email=body.get("contact_email"),
        created_by_user_id=body.get("created_by_user_id"),
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at or created_at or datetime.utcnow(),
        completed_at=completed_at,
        sync_scope=body.get("sync_scope", "public"),
    )
    session.merge(request_obj)

    comments = body.get("comments") or []
    for comment in comments:
        created_at = _parse_datetime(comment.get("created_at"))
        comment_obj = RequestComment(
            id=comment.get("id"),
            help_request_id=request_obj.id,
            user_id=comment.get("user_id"),
            body=comment.get("body", ""),
            created_at=created_at or datetime.utcnow(),
            sync_scope=comment.get("sync_scope", "public"),
        )
        session.merge(comment_obj)


def _import_invite(session: Session, body: dict[str, object]) -> None:
    created_at = _parse_datetime(body.get("created_at"))
    expires_at = _parse_datetime(body.get("expires_at"))
    invite = InviteToken(
        token=body.get("token"),
        created_by_user_id=body.get("created_by_user_id"),
        created_at=created_at or datetime.utcnow(),
        expires_at=expires_at,
        max_uses=body.get("max_uses", 1),
        use_count=body.get("use_count", 0),
        auto_approve=body.get("auto_approve", True),
        suggested_username=body.get("suggested_username"),
        suggested_bio=body.get("suggested_bio"),
        sync_scope=body.get("sync_scope", "public"),
    )
    session.merge(invite)


def _parse_datetime(value: object) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.rstrip("Z")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
