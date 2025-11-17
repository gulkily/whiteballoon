from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator


@dataclass
class ParsedComment:
    source_comment_id: int | None
    user_id: int | None
    username: str | None
    created_at: datetime | None
    sync_scope: str
    body: str


@dataclass
class ParsedRequest:
    source_request_id: int | None
    instance: str | None
    title: str
    description: str
    status: str
    sync_scope: str
    updated_at: datetime | None
    contact_email: str | None
    created_by_id: int | None
    created_by_username: str | None
    comments: list[ParsedComment]


@dataclass
class ParsedUser:
    user_id: int | None
    username: str | None
    sync_scope: str


def iter_request_files(bundle_root: Path) -> Iterator[Path]:
    request_dir = bundle_root / "requests"
    if not request_dir.exists():
        return iter(())
    return iter(sorted(request_dir.glob("*.sync.txt")))


def iter_user_files(bundle_root: Path) -> Iterator[Path]:
    users_dir = bundle_root / "users"
    if not users_dir.exists():
        return iter(())
    return iter(sorted(users_dir.glob("*.sync.txt")))


def parse_request_file(path: Path) -> ParsedRequest:
    headers, body_text = _parse_sync_file(path)
    description, comments = _parse_request_body(body_text)
    parsed_comments = [
        ParsedComment(
            source_comment_id=_maybe_int(comment.get("comment-id")),
            user_id=_maybe_int(comment.get("user-id")),
            username=comment.get("username"),
            created_at=_parse_datetime(comment.get("created-at")),
            sync_scope=comment.get("sync-scope", "public"),
            body=comment.get("body", ""),
        )
        for comment in comments
    ]
    return ParsedRequest(
        source_request_id=_maybe_int(headers.get("ID")),
        instance=headers.get("Instance"),
        title=headers.get("Title") or "",
        description=description,
        status=headers.get("Status", "open"),
        sync_scope=headers.get("Sync-Scope", "public"),
        updated_at=_parse_datetime(headers.get("Updated-At")),
        contact_email=headers.get("Contact-Email") or None,
        created_by_id=_maybe_int(headers.get("Created-By")),
        created_by_username=headers.get("Created-By-Username"),
        comments=parsed_comments,
    )


def parse_user_file(path: Path) -> ParsedUser:
    headers, _ = _parse_sync_file(path)
    return ParsedUser(
        user_id=_maybe_int(headers.get("ID")),
        username=headers.get("Username"),
        sync_scope=headers.get("Sync-Scope", "public"),
    )


def _parse_sync_file(path: Path) -> tuple[dict[str, str], str]:
    headers: dict[str, str] = {}
    body_lines: list[str] = []
    in_headers = True
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if in_headers:
                if not line.strip():
                    in_headers = False
                    continue
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
            else:
                body_lines.append(line)
    body = "\n".join(body_lines).rstrip()
    return headers, body


def _parse_request_body(body_text: str) -> tuple[str, list[dict[str, str]]]:
    if not body_text:
        return "", []
    description = body_text
    comments_section = ""
    marker = "\nComments:\n"
    if marker in body_text:
        description, comments_section = body_text.split(marker, 1)
    if description.startswith("Description:\n"):
        description = description[len("Description:\n") :]
    description = description.strip()

    comments: list[dict[str, str]] = []
    if comments_section:
        current: dict[str, str] | None = None
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
    parsed: list[dict[str, str]] = []
    for item in comments:
        body_lines = item.pop("body_lines", [])
        parsed.append(
            {
                **item,
                "body": "\n".join(body_lines).strip(),
            }
        )
    return description, parsed


def _maybe_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.rstrip("Z")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
