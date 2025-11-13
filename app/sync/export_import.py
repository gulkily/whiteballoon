from __future__ import annotations

from __future__ import annotations

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


def _write_sync_file(path: Path, headers: dict[str, str], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for key, value in headers.items():
            fh.write(f"{key}: {value}\n")
        fh.write("\n")
        if body:
            fh.write(body.rstrip() + "\n")


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
        body = ""
        headers = {
            "Entity": "user",
            "ID": str(user.id),
            "Instance": instance_id,
            "Schema-Version": SCHEMA_VERSION,
            "Updated-At": _iso(user.created_at) or "",
            "Sync-Scope": user.sync_scope,
            "Username": user.username,
            "Contact-Email": user.contact_email or "",
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
        body = _render_request_body(request_obj, comments_map.get(request_obj.id, []))
        headers = {
            "Entity": "request",
            "ID": str(request_obj.id),
            "Instance": instance_id,
            "Schema-Version": SCHEMA_VERSION,
            "Updated-At": _iso(request_obj.updated_at) or "",
            "Sync-Scope": request_obj.sync_scope,
            "Title": request_obj.title or "",
            "Status": request_obj.status,
            "Contact-Email": request_obj.contact_email or "",
            "Created-By": str(request_obj.created_by_user_id or ""),
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
        body = _render_invite_body(personalization)
        headers = {
            "Entity": "invite",
            "ID": invite.token,
            "Instance": instance_id,
            "Schema-Version": SCHEMA_VERSION,
            "Updated-At": _iso(invite.created_at) or "",
            "Sync-Scope": invite.sync_scope,
            "Created-By": str(invite.created_by_user_id or ""),
            "Max-Uses": str(invite.max_uses),
            "Use-Count": str(invite.use_count),
            "Auto-Approve": str(invite.auto_approve),
            "Suggested-Username": invite.suggested_username or "",
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


def _parse_sync_file(path: Path) -> tuple[dict[str, str], str]:
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
    return headers, body_text


def import_sync_data(session: Session, input_dir: Path) -> int:
    if not input_dir.exists():
        raise FileNotFoundError(f"Sync directory not found: {input_dir}")
    count = 0
    files = sorted(p for p in input_dir.rglob("*.sync.txt") if p.name != "manifest.sync.txt")
    for path in files:
        headers, body = _parse_sync_file(path)
        entity = headers.get("Entity")
        if entity == "user":
            _import_user(session, headers)
        elif entity == "request":
            _import_request(session, headers, body)
        elif entity == "invite":
            _import_invite(session, headers, body)
        count += 1
    session.commit()
    return count


def _import_user(session: Session, headers: dict[str, str]) -> None:
    created_at = _parse_datetime(headers.get("Updated-At"))
    user_id = _maybe_int(headers.get("ID"))
    username = headers.get("Username")
    contact_email_present = "Contact-Email" in headers
    contact_email = headers.get("Contact-Email") or None
    sync_scope = headers.get("Sync-Scope", "public")

    existing: User | None = None
    if user_id is not None:
        existing = session.get(User, user_id)
    if existing is None and username:
        existing = session.exec(select(User).where(User.username == username)).first()

    if existing:
        if username:
            existing.username = username
        if contact_email_present:
            existing.contact_email = contact_email
        if created_at:
            existing.created_at = created_at
        if sync_scope:
            existing.sync_scope = sync_scope
        session.add(existing)
    else:
        new_user = User(
            id=user_id,
            username=username,
            contact_email=contact_email,
            created_at=created_at or datetime.utcnow(),
            sync_scope=sync_scope,
        )
        session.add(new_user)


def _import_request(session: Session, headers: dict[str, str], body_text: str) -> None:
    created_at = _parse_datetime(headers.get("Created-At"))
    updated_at = _parse_datetime(headers.get("Updated-At"))
    completed_at = _parse_datetime(headers.get("Completed-At"))
    description, comments = _parse_request_body(body_text)
    request_obj = HelpRequest(
        id=_maybe_int(headers.get("ID")),
        title=headers.get("Title"),
        description=description,
        status=headers.get("Status", "open"),
        contact_email=headers.get("Contact-Email") or None,
        created_by_user_id=_maybe_int(headers.get("Created-By")),
        created_at=created_at or datetime.utcnow(),
        updated_at=updated_at or created_at or datetime.utcnow(),
        completed_at=completed_at,
        sync_scope=headers.get("Sync-Scope", "public"),
    )
    session.merge(request_obj)

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


def _import_invite(session: Session, headers: dict[str, str], body_text: str) -> None:
    created_at = _parse_datetime(headers.get("Updated-At"))
    expires_at = _parse_datetime(headers.get("Expires-At"))
    invite = InviteToken(
        token=headers.get("ID"),
        created_by_user_id=_maybe_int(headers.get("Created-By")),
        created_at=created_at or datetime.utcnow(),
        expires_at=expires_at,
        max_uses=_maybe_int(headers.get("Max-Uses")) or 1,
        use_count=_maybe_int(headers.get("Use-Count")) or 0,
        auto_approve=headers.get("Auto-Approve", "True").lower() == "true",
        suggested_username=headers.get("Suggested-Username"),
        sync_scope=headers.get("Sync-Scope", "public"),
    )
    session.merge(invite)

    if body_text.strip():
        # For now, body text contains personalization snippet; no import needed yet.
        pass


def _parse_datetime(value: object) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.rstrip("Z")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _maybe_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _render_request_body(request_obj: HelpRequest, comments: list[dict[str, object]]) -> str:
    lines: list[str] = ["Description:", request_obj.description or "", ""]
    if comments:
        lines.append("Comments:")
        for comment in comments:
            lines.append("---")
            lines.append(f"Comment-ID: {comment.get('id')}")
            lines.append(f"User-ID: {comment.get('user_id')}")
            lines.append(f"Username: {comment.get('username')}")
            lines.append(f"Created-At: {comment.get('created_at')}")
            lines.append(f"Sync-Scope: {comment.get('sync_scope')}")
            lines.append("")
            lines.append(comment.get("body") or "")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_invite_body(personalization: InvitePersonalization | None) -> str:
    if not personalization:
        return ""
    lines = []
    if personalization.gratitude_note:
        lines.append("Gratitude:")
        lines.append(personalization.gratitude_note)
        lines.append("")
    if personalization.support_message:
        lines.append("Support:")
        lines.append(personalization.support_message)
        lines.append("")
    if personalization.help_examples:
        lines.append("Help-Examples:")
        lines.append(personalization.help_examples)
        lines.append("")
    if personalization.fun_details:
        lines.append("Fun-Details:")
        lines.append(personalization.fun_details)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _parse_request_body(body_text: str) -> tuple[str, list[dict[str, object]]]:
    if not body_text:
        return "", []
    description = body_text
    comments_section = ""
    if "\nComments:\n" in body_text:
        description, comments_section = body_text.split("\nComments:\n", 1)
    if description.startswith("Description:\n"):
        description = description[len("Description:\n") :]
    description = description.strip()

    comments: list[dict[str, object]] = []
    if comments_section:
        current: dict[str, object] | None = None
        headers_done = False
        for line in comments_section.splitlines():
            if line.strip() == "---":
                if current:
                    comments.append(current)
                current = {"body_lines": []}
                headers_done = False
                continue
            if current is None:
                continue
            if not headers_done:
                if not line.strip():
                    headers_done = True
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    current[key.strip().lower()] = value.strip()
                continue
            current.setdefault("body_lines", []).append(line)
        if current:
            comments.append(current)
    parsed_comments: list[dict[str, object]] = []
    for item in comments:
        body_lines = item.pop("body_lines", [])
        parsed_comments.append(
            {
                "id": _maybe_int(item.get("comment-id")),
                "user_id": _maybe_int(item.get("user-id")),
                "username": item.get("username"),
                "created_at": item.get("created-at"),
                "sync_scope": item.get("sync-scope", "public"),
                "body": "\n".join(body_lines).strip(),
            }
        )
    return description, parsed_comments


def _parse_comment_meta(meta_line: str) -> dict[str, str]:
    parts = meta_line.split()
    meta: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        meta[key] = value
    return meta
