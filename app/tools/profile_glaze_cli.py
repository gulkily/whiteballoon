from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlmodel import Session, select

from app.db import get_engine
from app.models import User
from app.services import auth_service
from app.tools import comment_llm_processing
from app.tools import signal_profile_snapshot_cli as snapshot_cli

COMMENT_PROVIDER_CHOICES = ("dedalus", "mock")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.profile_glaze_cli",
        description=(
            "One-touch Signal profile glazing: refresh comment LLM analyses and bios in a single run."
        ),
    )
    parser.add_argument(
        "--username",
        action="append",
        dest="usernames",
        help="Process a specific username (repeatable)",
    )
    parser.add_argument(
        "--user-id",
        action="append",
        type=int,
        dest="user_ids",
        help="Process a specific user ID (repeatable)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every user with Signal metadata",
    )
    parser.add_argument(
        "--group-slug",
        help="Restrict Signal snapshots/glazing to a specific group slug",
    )
    parser.add_argument(
        "--comment-provider",
        choices=COMMENT_PROVIDER_CHOICES,
        default="dedalus",
        help="LLM provider for comment analyses",
    )
    parser.add_argument(
        "--comment-model",
        default=comment_llm_processing.DEFAULT_MODEL,
        help="Model alias for comment analyses",
    )
    parser.add_argument(
        "--comment-batch-size",
        type=int,
        default=comment_llm_processing.DEFAULT_BATCH_SIZE,
        help="Comment analyses per batch",
    )
    parser.add_argument(
        "--comment-limit",
        type=int,
        help="Maximum comments to analyze per user",
    )
    parser.add_argument(
        "--comment-max-spend-usd",
        type=float,
        help="Ceiling for comment analysis spend",
    )
    parser.add_argument(
        "--comment-label-prefix",
        default="profile-glaze",
        help="Prefix for generated snapshot labels when running the comment LLM",
    )
    parser.add_argument(
        "--comment-skip-existing",
        action="store_true",
        help="Skip comments that already have stored analyses",
    )
    parser.add_argument(
        "--glaze-model",
        default="openai/gpt-5-mini",
        help="Model alias passed to the glazing client",
    )
    parser.add_argument(
        "--glaze-dir",
        type=Path,
        default=snapshot_cli.GLAZE_DIR,
        help="Where to store glaze outputs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan comment batches but skip LLM execution and glaze writes",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if not (ns.usernames or ns.user_ids or ns.all):
        parser.error("Provide --username/--user-id or --all to select targets.")

    engine = get_engine()
    try:
        with Session(engine) as session:
            target_ids = _resolve_targets(session, ns.usernames or [], ns.user_ids or [], ns.all)
            if not target_ids:
                parser.error("No eligible users found for the supplied filters.")

            user_map = _load_usernames(session, target_ids)
            total_processed = 0
            for user_id in target_ids:
                label = _format_user_label(user_id, user_map)
                print(f"[profile-glaze] Processing {label}")
                comment_label = _build_comment_snapshot_label(
                    ns.comment_label_prefix, user_map.get(user_id)
                )
                comment_args = _build_comment_cli_args(ns, user_id, comment_label)
                rc = comment_llm_processing.main(comment_args)
                if rc != 0:
                    return rc
                if ns.dry_run:
                    continue
                glaze_stats, processed_users = snapshot_cli.glaze_users(
                    session,
                    [user_id],
                    dry_run=False,
                    group_slug=ns.group_slug,
                    model=ns.glaze_model,
                    glaze_dir=ns.glaze_dir,
                    max_users=None,
                    resume_skip=set(),
                )
                print(
                    f"[profile-glaze] Glaze complete for {label}: "
                    f"{glaze_stats.generated}/{glaze_stats.attempted} stored, {glaze_stats.guardrail_fallbacks} guardrail fallbacks"
                )
                total_processed += len(processed_users)
    except KeyboardInterrupt:
        print("\n[profile-glaze] Interrupted; exiting.")
        return 0

    if ns.dry_run:
        print("[profile-glaze] Dry run finished (no glazing performed).")
    else:
        print(f"[profile-glaze] Completed glazing for {total_processed} user(s).")
    return 0


def _resolve_targets(
    session: Session,
    usernames: list[str],
    user_ids: list[int],
    include_all: bool,
) -> list[int]:
    targets: set[int] = set()
    if include_all:
        targets.update(snapshot_cli._resolve_user_ids(session, [], True))
    for value in user_ids:
        if value:
            targets.add(int(value))
    for username in usernames:
        normalized = auth_service.normalize_username(username)
        user = session.exec(select(User).where(User.username == normalized)).first()
        if not user:
            print(f"[profile-glaze] Skipping unknown username '{username}'")
            continue
        targets.add(user.id)
    return sorted(targets)


def _load_usernames(session: Session, user_ids: Iterable[int]) -> dict[int, str]:
    ids = [int(uid) for uid in user_ids]
    if not ids:
        return {}
    rows = session.exec(select(User.id, User.username).where(User.id.in_(ids))).all()
    return {user_id: username or "" for user_id, username in rows}


def _format_user_label(user_id: int, user_map: dict[int, str]) -> str:
    username = user_map.get(user_id)
    if username:
        return f"user {user_id} (@{username})"
    return f"user {user_id}"


def _build_comment_snapshot_label(prefix: str, username: str | None) -> str:
    slug = (username or "user").lower().replace(" ", "-")
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{slug}-{timestamp}"


def _build_comment_cli_args(ns: argparse.Namespace, user_id: int, snapshot_label: str) -> list[str]:
    args = [
        "--snapshot-label",
        snapshot_label,
        "--batch-size",
        str(ns.comment_batch_size),
        "--user-id",
        str(user_id),
        "--provider",
        ns.comment_provider,
        "--model",
        ns.comment_model,
    ]
    if ns.comment_limit:
        args.extend(["--limit", str(ns.comment_limit)])
    if ns.comment_max_spend_usd:
        args.extend(["--max-spend-usd", str(ns.comment_max_spend_usd)])
    if not ns.comment_skip_existing:
        args.append("--include-processed")
    if not ns.dry_run:
        args.append("--execute")
    return args


if __name__ == "__main__":
    raise SystemExit(main())
