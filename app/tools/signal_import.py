"""Signal group import CLI helpers.

Parses Signal Desktop exports, maps chat participants to local users,
and seeds the chat as request comments inside the dev database.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from sqlmodel import Session, select

from app.db import get_engine
from app.models import HelpRequest, RequestComment, User, UserAttribute

SIGNAL_SOURCE_TAG = "signal_group_seed"
IMPORT_STATE_PATH = Path("storage/signal_import_state.json")


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _lookup_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.signal_import",
        description="Import a Signal Desktop group export into the local database.",
    )
    parser.add_argument(
        "--export-path",
        required=True,
        help="Path to the folder created by signal-export (contains data.json/jsonl files)",
    )
    parser.add_argument(
        "--group-name",
        help="Optional friendly name for the group (defaults to folder name)",
    )
    parser.add_argument(
        "--log-path",
        default="signal_group_import.log",
        help="File to append import logs to (default: signal_group_import.log in CWD)",
    )
    parser.add_argument(
        "--skip-attachments",
        action="store_true",
        help="Skip copying attachment metadata; useful when seeding text-only data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and log without writing to the database",
    )
    return parser


@dataclass
class SignalReaction:
    actor: str
    emoji: str


@dataclass
class SignalAttachment:
    name: str
    relative_path: str
    absolute_path: Path


@dataclass
class SignalMessage:
    key: str
    sent_at: datetime
    sender: str
    body: str
    quote: str
    sticker: str
    reactions: list[SignalReaction]
    attachments: list[SignalAttachment]


@dataclass
class SignalMember:
    name: str
    message_count: int


@dataclass
class SignalExport:
    group_name: str
    export_path: Path
    data_file: Path
    messages: list[SignalMessage]
    members: list[SignalMember]
    member_user_ids: dict[str, int] = field(default_factory=dict)

    @property
    def attachment_count(self) -> int:
        return sum(len(msg.attachments) for msg in self.messages)


@dataclass
class MemberMappingResult:
    name: str
    user_id: int | None
    action: str  # "existing", "created", or "pending"
    reason: str


@dataclass
class MemberMappingSummary:
    total_members: int
    existing_matches: int
    placeholders_created: int
    pending_creates: int
    created_examples: list[str] = field(default_factory=list)
    pending_examples: list[str] = field(default_factory=list)


@dataclass
class MessageImportSummary:
    total_messages: int
    inserted: int
    skipped_duplicates: int
    missing_user: int
    request_created: bool
    request_id: int | None


def _ensure_parent(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def _current_timestamp() -> str:
    return datetime.utcnow().isoformat()


def _write_log_entry(
    log_path: Path,
    *,
    export: SignalExport,
    member_summary: MemberMappingSummary,
    message_summary: MessageImportSummary,
    dry_run: bool,
) -> None:
    _ensure_parent(log_path)
    entry = {
        "timestamp": _current_timestamp(),
        "group": export.group_name,
        "dry_run": dry_run,
        "messages_total": len(export.messages),
        "attachments": export.attachment_count,
        "members": member_summary.total_members,
        "matched_members": member_summary.existing_matches,
        "new_placeholders": member_summary.placeholders_created,
        "inserted_comments": message_summary.inserted,
        "duplicates": message_summary.skipped_duplicates,
        "missing_user": message_summary.missing_user,
        "request_created": message_summary.request_created,
        "request_id": message_summary.request_id,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _load_import_state(path: Path = IMPORT_STATE_PATH) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_import_state(state: dict, path: Path = IMPORT_STATE_PATH) -> None:
    _ensure_parent(path)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _update_import_state(
    export: SignalExport,
    message_summary: MessageImportSummary,
    *,
    state_path: Path = IMPORT_STATE_PATH,
) -> None:
    state = _load_import_state(state_path)
    key = _slugify(export.group_name) or export.group_name
    state[key] = {
        "group_name": export.group_name,
        "last_run_at": _current_timestamp(),
        "message_total": len(export.messages),
        "last_message_at": export.messages[-1].sent_at.isoformat() if export.messages else None,
        "request_id": message_summary.request_id,
    }
    _save_import_state(state, state_path)


class SignalMemberMapper:
    """Resolve Signal senders to local User records."""

    SOURCE_ATTR_KEY = "signal_import_source"

    def __init__(self, session: Session, group_name: str, source_tag: str = SIGNAL_SOURCE_TAG):
        self.session = session
        self.group_name = group_name
        self.source_tag = source_tag
        self.group_slug = _slugify(group_name) or "signal-group"
        self.member_attr_key = f"signal_member_key:{self.group_slug}"
        self.display_attr_key = f"signal_display_name:{self.group_slug}"
        self.group_attr_key = f"signal_import_group:{self.group_slug}"
        self._username_index = self._load_username_index()

    def _load_username_index(self) -> dict[str, int]:
        index: dict[str, int] = {}
        rows = self.session.exec(select(User.id, User.username)).all()
        for user_id, username in rows:
            if username:
                index[username.lower()] = user_id
        return index

    def map_members(
        self, members: Iterable[SignalMember], *, dry_run: bool
    ) -> tuple[dict[str, int], list[MemberMappingResult]]:
        lookup: dict[str, int] = {}
        results: list[MemberMappingResult] = []
        for member in members:
            normalized_slug = _slugify(member.name) or f"member-{member.message_count}"
            attr_match = self._lookup_by_attribute(normalized_slug)
            if attr_match:
                key = _lookup_key(member.name)
                lookup[key] = attr_match
                results.append(MemberMappingResult(member.name, attr_match, "existing", "attribute"))
                continue

            username_match = self._lookup_by_username(member.name)
            if username_match:
                if not dry_run:
                    self._attach_metadata(username_match, normalized_slug, member.name, add_source=False)
                key = _lookup_key(member.name)
                lookup[key] = username_match
                results.append(MemberMappingResult(member.name, username_match, "existing", "username"))
                continue

            if dry_run:
                results.append(
                    MemberMappingResult(member.name, None, "pending", "would create placeholder")
                )
                continue

            user = self._create_placeholder(member, normalized_slug)
            key = _lookup_key(member.name)
            lookup[key] = user.id
            results.append(MemberMappingResult(member.name, user.id, "created", "placeholder"))
        return lookup, results

    def _lookup_by_attribute(self, slug_value: str) -> int | None:
        stmt = select(UserAttribute).where(
            UserAttribute.key == self.member_attr_key,
            UserAttribute.value == slug_value,
        )
        attr = self.session.exec(stmt).first()
        return attr.user_id if attr else None

    def _lookup_by_username(self, member_name: str) -> int | None:
        for candidate in self._candidate_usernames(member_name):
            user_id = self._username_index.get(candidate.lower())
            if user_id:
                return user_id
        return None

    def _candidate_usernames(self, member_name: str) -> list[str]:
        slug = _slugify(member_name)
        collapsed = slug.replace("-", "") if slug else ""
        raw = member_name.strip()
        candidates = []
        if raw:
            candidates.append(raw)
        if slug:
            candidates.append(slug)
            candidates.append(f"signal-{slug}")
        if collapsed and collapsed not in candidates:
            candidates.append(collapsed)
        return candidates

    def _attach_metadata(self, user_id: int, slug_value: str, display_name: str, *, add_source: bool) -> None:
        self._upsert_attribute(user_id, self.member_attr_key, slug_value)
        self._upsert_attribute(user_id, self.display_attr_key, display_name)
        self._upsert_attribute(user_id, self.group_attr_key, self.group_name)
        if add_source:
            self._upsert_attribute(user_id, self.SOURCE_ATTR_KEY, self.source_tag)

    def _upsert_attribute(self, user_id: int, key: str, value: str) -> None:
        stmt = select(UserAttribute).where(
            UserAttribute.user_id == user_id,
            UserAttribute.key == key,
        )
        attr = self.session.exec(stmt).first()
        if attr:
            attr.value = value
            attr.updated_at = datetime.utcnow()
        else:
            self.session.add(UserAttribute(user_id=user_id, key=key, value=value))

    def _create_placeholder(self, member: SignalMember, slug_value: str) -> User:
        username = self._generate_username(slug_value)
        user = User(username=username)
        self.session.add(user)
        self.session.flush()
        self._username_index[username.lower()] = user.id
        self._attach_metadata(user.id, slug_value, member.name, add_source=True)
        return user

    def _generate_username(self, slug_value: str) -> str:
        base = f"signal-{self.group_slug}-{slug_value}".strip("-") or f"signal-{self.group_slug}"
        candidate = base
        suffix = 1
        while self._username_index.get(candidate.lower()):
            suffix += 1
            candidate = f"{base}-{suffix}"
        return candidate


def _validate_export_path(raw_path: str) -> Path:
    export_path = Path(raw_path).expanduser().resolve()
    if not export_path.exists():
        raise FileNotFoundError(f"Export path not found: {export_path}")
    if not export_path.is_dir():
        raise NotADirectoryError(f"Export path must be a directory: {export_path}")
    return export_path


def _locate_data_file(export_path: Path) -> Path:
    candidate = export_path / "data.json"
    if candidate.exists():
        return candidate
    jsonl_files = sorted(export_path.glob("*.jsonl"))
    if jsonl_files:
        return jsonl_files[0]
    raise FileNotFoundError(
        f"Could not find data.json or *.jsonl inside {export_path}. Verify the signal-export output."
    )


def _iter_json_records(data_file: Path) -> Iterator[dict]:
    with data_file.open("r", encoding="utf-8") as handle:
        start_pos = handle.tell()
        first_char: str | None = None
        while True:
            char = handle.read(1)
            if not char:
                break
            if not char.isspace():
                first_char = char
                break
        handle.seek(start_pos)
        if not first_char:
            return
        if first_char == "[":
            data = json.load(handle)
            for item in data:
                if isinstance(item, dict):
                    yield item
            return
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _parse_reactions(raw: Sequence | None) -> list[SignalReaction]:
    reactions: list[SignalReaction] = []
    if not raw:
        return reactions
    for entry in raw:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        actor = str(entry[0])
        emoji = str(entry[1])
        reactions.append(SignalReaction(actor=actor, emoji=emoji))
    return reactions


def _parse_attachments(raw: Sequence[dict] | None, export_path: Path) -> list[SignalAttachment]:
    attachments: list[SignalAttachment] = []
    if not raw:
        return attachments
    for entry in raw:
        name = str(entry.get("name", ""))
        rel_path = str(entry.get("path", ""))
        abs_path = (export_path / rel_path).resolve()
        attachments.append(
            SignalAttachment(name=name, relative_path=rel_path, absolute_path=abs_path)
        )
    return attachments


def _parse_messages(
    export_path: Path,
    data_file: Path,
    *,
    skip_attachments: bool,
) -> list[SignalMessage]:
    messages: list[SignalMessage] = []
    for idx, payload in enumerate(_iter_json_records(data_file)):
        if not isinstance(payload, dict):
            continue
        sent_at_raw = payload.get("date") or payload.get("timestamp")
        if sent_at_raw is None:
            continue
        sent_at: datetime
        try:
            sent_at = datetime.fromisoformat(str(sent_at_raw))
        except ValueError:
            try:
                sent_at = datetime.fromtimestamp(float(sent_at_raw) / 1000.0)
            except Exception:
                continue
        sender = str(payload.get("sender") or payload.get("profile") or "Unknown")
        body = str(payload.get("body") or "").rstrip()
        quote = str(payload.get("quote") or "")
        sticker = str(payload.get("sticker") or "")
        reactions = _parse_reactions(payload.get("reactions"))
        attachments = (
            []
            if skip_attachments
            else _parse_attachments(payload.get("attachments"), export_path)
        )
        key = str(payload.get("id")) if payload.get("id") else f"{sent_at.isoformat()}::{sender}::{idx}"
        messages.append(
            SignalMessage(
                key=key,
                sent_at=sent_at,
                sender=sender,
                body=body,
                quote=quote,
                sticker=sticker,
                reactions=reactions,
                attachments=attachments,
            )
        )
    return messages


def _build_members(messages: Iterable[SignalMessage]) -> list[SignalMember]:
    counter = Counter(msg.sender for msg in messages)
    members = [SignalMember(name=name, message_count=count) for name, count in counter.items()]
    members.sort(key=lambda m: m.message_count, reverse=True)
    return members


def load_signal_export(
    export_path: Path,
    *,
    group_name: str,
    skip_attachments: bool,
) -> SignalExport:
    data_file = _locate_data_file(export_path)
    messages = _parse_messages(export_path, data_file, skip_attachments=skip_attachments)
    members = _build_members(messages)
    return SignalExport(
        group_name=group_name,
        export_path=export_path,
        data_file=data_file,
        messages=messages,
        members=members,
    )


def _summarize_member_results(results: list[MemberMappingResult]) -> MemberMappingSummary:
    created_examples = [res.name for res in results if res.action == "created"][:5]
    pending_examples = [res.name for res in results if res.action == "pending"][:5]
    return MemberMappingSummary(
        total_members=len(results),
        existing_matches=sum(1 for res in results if res.action == "existing"),
        placeholders_created=sum(1 for res in results if res.action == "created"),
        pending_creates=sum(1 for res in results if res.action == "pending"),
        created_examples=created_examples,
        pending_examples=pending_examples,
    )


def _group_request_title(group_name: str) -> str:
    return f"[Signal] {group_name}".strip()


def _group_request_description(group_name: str) -> str:
    return f"Signal group seed for {group_name}"[:4000]


def _format_message_body(message: SignalMessage) -> str:
    lines: list[str] = []
    quote = message.quote.strip()
    if quote:
        for raw_line in quote.splitlines():
            line = raw_line.strip()
            prefix = f"> {line}" if line else ">"
            lines.append(prefix.rstrip())
        lines.append("")

    text = message.body.strip()
    if text:
        lines.append(text)
    if not text and not message.attachments:
        lines.append("(no text)")

    if message.attachments:
        attachment_names = [att.name or Path(att.relative_path).name for att in message.attachments]
        lines.append("")
        lines.append(f"[attachments: {', '.join(attachment_names)}]")

    if message.reactions:
        reactions = ", ".join(f"{reaction.actor} {reaction.emoji}" for reaction in message.reactions)
        lines.append(f"(Reactions: {reactions})")

    body = "\n".join(lines).strip()
    return body or "(no text)"


def _load_existing_comment_keys(session: Session, request_id: int) -> set[tuple[int, str, datetime]]:
    rows = session.exec(
        select(RequestComment.user_id, RequestComment.body, RequestComment.created_at)
        .where(RequestComment.help_request_id == request_id)
    ).all()
    return {(user_id, body, created_at) for user_id, body, created_at in rows}


def _ensure_group_request(
    session: Session,
    group_name: str,
    *,
    dry_run: bool,
) -> tuple[HelpRequest, bool]:
    title = _group_request_title(group_name)
    stmt = select(HelpRequest).where(HelpRequest.title == title)
    existing = session.exec(stmt).first()
    if existing:
        return existing, False

    now = datetime.utcnow()
    request = HelpRequest(
        title=title,
        description=_group_request_description(group_name),
        status="open",
        created_at=now,
        updated_at=now,
        sync_scope="private",
    )
    if dry_run:
        return request, True

    session.add(request)
    session.commit()
    session.refresh(request)
    return request, True


def ingest_messages(export: SignalExport, *, dry_run: bool) -> MessageImportSummary:
    with Session(get_engine()) as session:
        request, created = _ensure_group_request(session, export.group_name, dry_run=dry_run)
        existing_keys: set[tuple[int, str, datetime]] = set()
        if request.id:
            existing_keys = _load_existing_comment_keys(session, request.id)

        inserted = 0
        duplicates = 0
        missing_user = 0

        for message in export.messages:
            user_id = export.member_user_ids.get(_lookup_key(message.sender))
            if not user_id:
                missing_user += 1
                continue

            body = _format_message_body(message)
            dedupe_key = (user_id, body, message.sent_at)
            if request.id and dedupe_key in existing_keys:
                duplicates += 1
                continue

            if dry_run or not request.id:
                inserted += 1
                continue

            comment = RequestComment(
                help_request_id=request.id,
                user_id=user_id,
                body=body,
                created_at=message.sent_at,
                sync_scope="private",
            )
            session.add(comment)
            existing_keys.add(dedupe_key)
            inserted += 1

        if not dry_run:
            session.commit()

        return MessageImportSummary(
            total_messages=len(export.messages),
            inserted=inserted,
            skipped_duplicates=duplicates,
            missing_user=missing_user,
            request_created=created,
            request_id=request.id if request.id else None,
        )


def map_signal_members(export: SignalExport, *, dry_run: bool) -> MemberMappingSummary:
    with Session(get_engine()) as session:
        mapper = SignalMemberMapper(session, export.group_name)
        member_lookup, results = mapper.map_members(export.members, dry_run=dry_run)
        if not dry_run:
            session.commit()
        export.member_user_ids = member_lookup
    return _summarize_member_results(results)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    try:
        export_path = _validate_export_path(ns.export_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"[signal-import] {exc}", file=sys.stderr)
        return 1

    group_name = ns.group_name or export_path.name
    try:
        export = load_signal_export(
            export_path,
            group_name=group_name,
            skip_attachments=ns.skip_attachments,
        )
    except FileNotFoundError as exc:
        print(f"[signal-import] {exc}", file=sys.stderr)
        return 1

    member_summary = map_signal_members(export, dry_run=ns.dry_run)
    message_summary = ingest_messages(export, dry_run=ns.dry_run)
    log_path = Path(ns.log_path).expanduser().resolve()
    state_path = IMPORT_STATE_PATH.resolve()
    if not ns.dry_run:
        _write_log_entry(
            log_path,
            export=export,
            member_summary=member_summary,
            message_summary=message_summary,
            dry_run=False,
        )
        _update_import_state(export, message_summary, state_path=state_path)

    print("[signal-import] Parsed Signal export")
    print(f"  export path    : {export.export_path}")
    print(f"  data file      : {export.data_file.name}")
    print(f"  group name     : {export.group_name}")
    print(f"  messages       : {len(export.messages):,}")
    if export.messages:
        first = export.messages[0].sent_at.isoformat()
        last = export.messages[-1].sent_at.isoformat()
        print(f"  timeframe      : {first}  →  {last}")
    print(f"  unique senders : {len(export.members):,}")
    top_members = export.members[:5]
    if top_members:
        print("  top senders    :")
        for member in top_members:
            print(f"    - {member.name}: {member.message_count}")
    print(f"  attachments    : {export.attachment_count:,} (ignored: {'yes' if ns.skip_attachments else 'no'})")
    print(f"  member mapping : {member_summary.existing_matches} matched, "
          f"{member_summary.placeholders_created} new, {member_summary.pending_creates} pending")
    if member_summary.created_examples:
        print("  new placeholders:")
        for name in member_summary.created_examples:
            print(f"    - {name}")
    elif member_summary.pending_examples:
        print("  pending creates:")
        for name in member_summary.pending_examples:
            print(f"    - {name}")
    print(
        "  seed request   : "
        + ("created" if message_summary.request_created else "reused existing")
    )
    print(
        "  message import : "
        f"{message_summary.inserted} new, {message_summary.skipped_duplicates} duplicates skipped, "
        f"{message_summary.missing_user} missing user mappings"
    )
    print(f"  dry run        : {'yes' if ns.dry_run else 'no'}")
    print(f"  log path       : {log_path}")
    if ns.dry_run:
        print(f"  state file     : {state_path} (unchanged)")
    else:
        print(f"  state file     : {state_path}")
    if ns.dry_run:
        print("Dry-run complete; no database writes performed.")
    else:
        print("Import complete; messages available via the seed request.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
