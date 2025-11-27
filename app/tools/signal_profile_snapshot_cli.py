from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from sqlmodel import Session, select

from app.db import get_engine
from app.models import RequestComment, User, UserAttribute
from app.services import (
    comment_llm_insights_service,
    signal_profile_snapshot_service,
    user_profile_highlight_service,
)
from app.services.signal_profile_bio_client import SignalProfileBioLLM
from app.services.signal_profile_bio_service import BioPayload
from app.services.signal_profile_snapshot import SignalProfileSnapshot

SNAPSHOT_DIR = Path("storage/signal_profiles")
RUN_LOG_PATH = Path("storage/signal_profile_snapshot.log")
STATSD_SNAPSHOT_METRIC = "signal_glaze.snapshots_generated"
STATSD_GLAZE_METRIC = "signal_glaze.bios_generated"
STATSD_GUARDRAIL_METRIC = "signal_glaze.guardrail_fallbacks"
STATSD_STALE_METRIC = "signal_glaze.highlights_stale"
GLAZE_DIR = Path("storage/signal_profiles/glazed")
GLAZE_LOG_PATH = Path("storage/signal_profile_glaze.log")
MAX_ANALYSIS_COMMENTS = 12


@dataclass
class SnapshotStats:
    attempted: int = 0
    generated: int = 0
    skipped: int = 0


@dataclass
class GlazeStats:
    attempted: int = 0
    generated: int = 0
    skipped: int = 0
    guardrail_fallbacks: int = 0


@dataclass
class FreshnessStats:
    inspected: int = 0
    marked: int = 0
    skipped: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wb signal-profile snapshot",
        description="Generate Signal identity snapshots for one or more users",
    )
    parser.add_argument(
        "action",
        choices=["snapshot", "glaze", "freshness"],
        help="Subcommand to run (snapshot, glaze, or freshness)",
    )
    parser.add_argument("--user", type=int, action="append", help="Specific user ID(s) to snapshot")
    parser.add_argument("--all", action="store_true", help="Process every user with Signal metadata")
    parser.add_argument("--group-slug", help="Limit snapshots to a specific Signal group slug")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SNAPSHOT_DIR,
        help="Directory for JSON snapshots (default: storage/signal_profiles)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--model", help="LLM model alias for glazing")
    parser.add_argument(
        "--glaze-dir",
        type=Path,
        default=GLAZE_DIR,
        help="Directory for glazed bios (default: storage/signal_profiles/glazed)",
    )
    parser.add_argument(
        "--max-users",
        type=int,
        help="Process at most this many users (glaze mode)",
    )
    parser.add_argument(
        "--resume-file",
        type=Path,
        help="Optional JSON file tracking glazed user IDs for resume support",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.all and not args.user:
        parser.error("Provide --user or --all to select targets")

    started_at = time.perf_counter()
    with Session(get_engine()) as session:
        user_ids = _resolve_user_ids(session, args.user or [], args.all)
        if not user_ids:
            print("[signal-profile] No eligible users found.")
            return 0

        if args.action == "snapshot":
            stats = snapshot_users(
                session,
                user_ids,
                output_dir=args.output_dir,
                dry_run=args.dry_run,
                group_slug=args.group_slug,
            )
            duration = time.perf_counter() - started_at
            _write_run_log(stats, duration, args.dry_run, args.output_dir, len(user_ids))
            _emit_statsd(STATSD_SNAPSHOT_METRIC, stats.generated)
            status = "dry run" if args.dry_run else "written"
            print(
                f"[signal-profile] {stats.generated}/{stats.attempted} snapshots {status}. "
                f"{stats.skipped} skipped (no data)."
            )
            return 0

        elif args.action == "glaze":
            resume_skip = _load_resume_ids(args.resume_file) if args.resume_file else set()
            glaze_stats, processed_users = glaze_users(
                session,
                user_ids,
                dry_run=args.dry_run,
                group_slug=args.group_slug,
                model=args.model,
                glaze_dir=args.glaze_dir,
                max_users=args.max_users,
                resume_skip=resume_skip,
            )
            duration = time.perf_counter() - started_at
            _write_glaze_log(glaze_stats, duration, args.dry_run, args.glaze_dir)
            _emit_statsd(STATSD_GLAZE_METRIC, glaze_stats.generated)
            _emit_statsd(STATSD_GUARDRAIL_METRIC, glaze_stats.guardrail_fallbacks)
            if args.resume_file and not args.dry_run:
                _update_resume_file(args.resume_file, resume_skip, processed_users)
            suffix = "dry run" if args.dry_run else "written"
            print(
                f"[signal-profile] Glazed {glaze_stats.generated}/{glaze_stats.attempted} users ({suffix}); "
                f"{glaze_stats.skipped} skipped, {glaze_stats.guardrail_fallbacks} guardrail fallbacks."
            )
            return 0

        fresh_stats = freshness_scan(
            session,
            user_ids if not args.all else None,
            dry_run=args.dry_run,
            group_slug=args.group_slug,
        )
        _emit_statsd(STATSD_STALE_METRIC, fresh_stats.marked if not args.dry_run else 0)
        status = "dry run" if args.dry_run else "updated"
        print(
            f"[signal-profile] Freshness scan: inspected {fresh_stats.inspected}, marked {fresh_stats.marked} stale ({status}), "
            f"skipped {fresh_stats.skipped}."
        )
        return 0
        # Freshness branch above returns. (will add code afterward?)


def _resolve_user_ids(session: Session, explicit_ids: list[int], include_all: bool) -> list[int]:
    if include_all:
        stmt = (
            select(UserAttribute.user_id)
            .where(UserAttribute.key.like("signal_import_group:%"))
            .distinct()
        )
        rows = list(session.exec(stmt).all())
    else:
        rows = []
    user_ids = set(explicit_ids or [])
    user_ids.update(rows)
    return sorted(user_ids)


def snapshot_users(
    session: Session,
    user_ids: Iterable[int],
    *,
    output_dir: Path = SNAPSHOT_DIR,
    dry_run: bool = False,
    group_slug: str | None = None,
    builder: Callable[[Session, int, str | None], SignalProfileSnapshot | None]
    = signal_profile_snapshot_service.build_snapshot,
) -> SnapshotStats:
    stats = SnapshotStats()
    user_list = list(dict.fromkeys(user_ids))
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    for user_id in user_list:
        stats.attempted += 1
        snapshot = builder(session, user_id, group_slug=group_slug)
        if not snapshot:
            stats.skipped += 1
            print(f"  · user {user_id}: no Signal snapshot available")
            continue
        stats.generated += 1
        output_path = output_dir / f"{snapshot.user_id}-{snapshot.group_slug}.json"
        if dry_run:
            print(f"  · user {user_id}: would write {output_path}")
            continue
        payload = snapshot.to_dict()
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"  · user {user_id}: wrote {output_path}")
    return stats


def glaze_users(
    session: Session,
    user_ids: Iterable[int],
    *,
    dry_run: bool,
    group_slug: str | None,
    model: str | None,
    glaze_dir: Path,
    max_users: int | None,
    resume_skip: set[int],
) -> tuple[GlazeStats, list[int]]:
    stats = GlazeStats()
    targets = list(dict.fromkeys(user_ids))
    if max_users is not None:
        targets = targets[: max(0, max_users)]
    if not dry_run:
        glaze_dir.mkdir(parents=True, exist_ok=True)
    user_map = _load_usernames(session, targets)

    try:
        client = SignalProfileBioLLM(model=model)
    except RuntimeError as exc:
        raise SystemExit(str(exc))

    processed: list[int] = []
    for user_id in targets:
        user_label = _format_user_label(user_id, user_map)
        if user_id in resume_skip:
            stats.skipped += 1
            print(f"  · {user_label}: skipped (already glazed via resume file)")
            continue
        highlight = user_profile_highlight_service.get(session, user_id)
        if highlight and highlight.manual_override and not highlight.is_stale:
            stats.skipped += 1
            print(f"  · {user_label}: manual override active; skipping glaze")
            continue
        stats.attempted += 1
        snapshot = signal_profile_snapshot_service.build_snapshot(
            session,
            user_id,
            group_slug=group_slug,
        )
        if not snapshot:
            stats.skipped += 1
            print(f"  · {user_label}: no snapshot available for glazing")
            continue
        comment_ids = _recent_comment_ids(session, user_id, snapshot.request_ids)
        analyses = _load_analyses(comment_ids)
        result = client.generate(snapshot, analyses)
        if result.guardrail_issues:
            stats.guardrail_fallbacks += 1
        if dry_run:
            preview = result.payload.bio_paragraphs[0] if result.payload.bio_paragraphs else "(no copy)"
            print(
                f"  · {user_label}: would glaze → {preview[:80]}... | issues={result.guardrail_issues}"
            )
            stats.generated += 1
            processed.append(user_id)
            continue

        output_path = glaze_dir / f"{snapshot.user_id}-{snapshot.group_slug}.glaze.json"
        payload = {
            "user_id": snapshot.user_id,
            "group_slug": snapshot.group_slug,
            "payload": result.payload.to_dict(),
            "guardrail_issues": result.guardrail_issues,
            "raw_response": result.raw_response,
        }
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"  · {user_label}: glazed → {output_path}")
        stats.generated += 1
        processed.append(user_id)
        highlight_meta = user_profile_highlight_service.HighlightMeta(
            source_group=snapshot.group_slug,
            llm_model=model,
            snapshot_last_seen_at=snapshot.last_seen_at,
            guardrail_issues=result.guardrail_issues,
        )
        stored = user_profile_highlight_service.upsert_auto(
            session,
            user_id=user_id,
            bio_paragraphs=result.payload.bio_paragraphs,
            proof_points=_proof_points_to_dicts(result.payload.proof_points),
            quotes=result.payload.quotes,
            confidence_note=result.payload.confidence_note,
            snapshot_hash=_snapshot_hash(snapshot),
            meta=highlight_meta,
        )
        session.commit()
        if stored.manual_override:
            print("    · DB highlight locked (manual) – skipped update")
        else:
            print("    · DB highlight stored; stale=%s" % stored.is_stale)
    return stats, processed


def freshness_scan(
    session: Session,
    user_ids: list[int] | None,
    *,
    dry_run: bool,
    group_slug: str | None,
) -> FreshnessStats:
    stats = FreshnessStats()
    highlights = (
        user_profile_highlight_service.list_highlights(session, user_ids)
        if user_ids
        else user_profile_highlight_service.list_highlights(session, None)
    )
    for record in highlights:
        stats.inspected += 1
        if record.manual_override:
            stats.skipped += 1
            continue
        reason: str | None = None
        now = datetime.utcnow()
        if record.stale_after and now > record.stale_after:
            reason = "stale-after"
        snapshot = signal_profile_snapshot_service.build_snapshot(
            session,
            record.user_id,
            group_slug=group_slug or record.source_group,
        )
        if not snapshot:
            continue
        new_hash = _snapshot_hash(snapshot)
        if snapshot.last_seen_at > record.snapshot_last_seen_at:
            reason = reason or "new-messages"
        elif new_hash != record.snapshot_hash:
            reason = reason or "snapshot-mismatch"

        if reason:
            if not dry_run:
                user_profile_highlight_service.mark_stale(
                    session, user_id=record.user_id, reason=reason
                )
                session.commit()
            stats.marked += 1
    return stats


def _write_run_log(
    stats: SnapshotStats,
    duration_seconds: float,
    dry_run: bool,
    output_dir: Path,
    target_users: int,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted": stats.attempted,
        "generated": stats.generated,
        "skipped": stats.skipped,
        "duration_seconds": round(duration_seconds, 3),
        "dry_run": dry_run,
        "output_dir": str(output_dir),
        "target_users": target_users,
    }
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _write_glaze_log(stats: GlazeStats, duration_seconds: float, dry_run: bool, output_dir: Path) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted": stats.attempted,
        "generated": stats.generated,
        "skipped": stats.skipped,
        "guardrail_fallbacks": stats.guardrail_fallbacks,
        "duration_seconds": round(duration_seconds, 3),
        "dry_run": dry_run,
        "output_dir": str(output_dir),
    }
    GLAZE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GLAZE_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _load_resume_ids(path: Path | None) -> set[int]:
    if not path or not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(payload, list):
        return {int(value) for value in payload if isinstance(value, int)}
    return set()


def _load_usernames(session: Session, user_ids: Iterable[int]) -> dict[int, str]:
    ids = [int(uid) for uid in user_ids if uid]
    if not ids:
        return {}
    stmt = select(User.id, User.username).where(User.id.in_(ids))
    rows = session.exec(stmt).all()
    return {user_id: username or "" for user_id, username in rows}


def _format_user_label(user_id: int, user_map: dict[int, str]) -> str:
    username = user_map.get(user_id)
    if username:
        return f"user {user_id} (@{username})"
    return f"user {user_id}"


def _update_resume_file(path: Path, existing: set[int], processed: list[int]) -> None:
    combined = sorted(existing.union(processed))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")


def _recent_comment_ids(
    session: Session, user_id: int, request_ids: Iterable[int]
) -> list[int]:
    if not request_ids:
        return []
    stmt = (
        select(RequestComment.id)
        .where(
            RequestComment.user_id == user_id,
            RequestComment.help_request_id.in_(list(request_ids)),
        )
        .order_by(RequestComment.created_at.desc(), RequestComment.id.desc())
        .limit(MAX_ANALYSIS_COMMENTS)
    )
    return [int(comment_id) for comment_id in session.exec(stmt).all()]


def _load_analyses(comment_ids: Iterable[int]):
    insights = []
    for comment_id in comment_ids:
        insight = comment_llm_insights_service.get_analysis_by_comment_id(comment_id)
        if insight:
            insights.append(insight)
    return list(reversed(insights))  # chronological order for prompt clarity


def _proof_points_to_dicts(items):
    result = []
    for item in items:
        if hasattr(item, "to_dict"):
            result.append(item.to_dict())
        elif isinstance(item, dict):
            result.append(item)
    return result


def _snapshot_hash(snapshot: SignalProfileSnapshot) -> str:
    payload = json.dumps(snapshot.to_dict(), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _emit_statsd(metric: str, value: int) -> None:
    host = os.getenv("STATSD_HOST")
    if not host:
        return
    port = int(os.getenv("STATSD_PORT", "8125"))
    payload = f"{metric}:{value}|c".encode("utf-8")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(payload, (host, port))
    except OSError:
        pass
    finally:
        with contextlib.suppress(Exception):
            sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
