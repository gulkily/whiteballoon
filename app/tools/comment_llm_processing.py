from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Sequence

from sqlalchemy.sql import Select
from sqlmodel import Session, select

from app.db import get_engine
from app.models import RequestComment


MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 25
DEFAULT_BATCH_SIZE = 10
DEFAULT_INSTRUCTIONS_TOKENS = 450
DEFAULT_PER_COMMENT_PREFIX_TOKENS = 24
DEFAULT_RESPONSE_TOKENS_PER_COMMENT = 120
DEFAULT_INPUT_COST_PER_1K = 0.00015  # Rough gpt-4o-mini rate
DEFAULT_OUTPUT_COST_PER_1K = 0.0006


@dataclass(frozen=True)
class SnapshotFilters:
    min_id: int | None = None
    max_id: int | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    help_request_ids: tuple[int, ...] = tuple()
    include_deleted: bool = False
    resume_after_id: int | None = None


@dataclass(frozen=True)
class BatchEstimates:
    batch_index: int
    comment_ids: list[int]
    comment_count: int
    estimated_input_tokens: int
    estimated_output_tokens: int


@dataclass(frozen=True)
class RunSummary:
    snapshot_label: str
    total_comments: int
    total_batches: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    batch_size: int
    filters: SnapshotFilters
    batches: list[BatchEstimates]


@dataclass(frozen=True)
class EstimationConfig:
    instructions_tokens: int
    per_comment_prefix_tokens: int
    response_tokens_per_comment: int
    input_cost_per_1k: float
    output_cost_per_1k: float


@dataclass(frozen=True)
class CommentPayload:
    id: int
    help_request_id: int
    user_id: int
    created_at: datetime
    body: str


class CommentBatchPlanner:
    def __init__(
        self,
        *,
        session: Session,
        filters: SnapshotFilters,
        batch_size: int,
        max_comments: int | None,
        estimation_config: EstimationConfig,
        snapshot_label: str,
    ) -> None:
        if not MIN_BATCH_SIZE <= batch_size <= MAX_BATCH_SIZE:
            raise ValueError(f"Batch size must be between {MIN_BATCH_SIZE} and {MAX_BATCH_SIZE}")
        self.session = session
        self.filters = filters
        self.batch_size = batch_size
        self.max_comments = max_comments
        self.estimation_config = estimation_config
        self.snapshot_label = snapshot_label

    def plan(self) -> RunSummary:
        rows = list(self._load_comments())
        batches = list(self._chunk(rows))
        estimates = [self._estimate_batch(idx, batch) for idx, batch in enumerate(batches, start=1)]
        total_input = sum(item.estimated_input_tokens for item in estimates)
        total_output = sum(item.estimated_output_tokens for item in estimates)
        cost = self._estimate_cost(total_input, total_output)
        return RunSummary(
            snapshot_label=self.snapshot_label,
            total_comments=len(rows),
            total_batches=len(estimates),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            estimated_cost_usd=cost,
            batch_size=self.batch_size,
            filters=self.filters,
            batches=estimates,
        )

    def _load_comments(self) -> Iterable[CommentPayload]:
        stmt = select(RequestComment)
        stmt = stmt.order_by(RequestComment.created_at.asc(), RequestComment.id.asc())
        stmt = self._apply_filters(stmt)
        if self.max_comments:
            stmt = stmt.limit(self.max_comments)
        for comment in self.session.exec(stmt):
            yield CommentPayload(
                id=comment.id or 0,
                help_request_id=comment.help_request_id,
                user_id=comment.user_id,
                created_at=comment.created_at,
                body=comment.body or "",
            )

    def _apply_filters(self, stmt: Select) -> Select:
        filters = self.filters
        if filters.min_id:
            stmt = stmt.where(RequestComment.id >= filters.min_id)
        if filters.max_id:
            stmt = stmt.where(RequestComment.id <= filters.max_id)
        if filters.resume_after_id:
            stmt = stmt.where(RequestComment.id > filters.resume_after_id)
        if filters.created_after:
            stmt = stmt.where(RequestComment.created_at >= filters.created_after)
        if filters.created_before:
            stmt = stmt.where(RequestComment.created_at <= filters.created_before)
        if filters.help_request_ids:
            stmt = stmt.where(RequestComment.help_request_id.in_(filters.help_request_ids))
        if not filters.include_deleted:
            stmt = stmt.where(RequestComment.deleted_at.is_(None))
        return stmt

    def _chunk(self, comments: Sequence[CommentPayload]) -> Iterable[List[CommentPayload]]:
        if not comments:
            return []
        chunks: list[list[CommentPayload]] = []
        for start in range(0, len(comments), self.batch_size):
            chunks.append(list(comments[start : start + self.batch_size]))
        return chunks

    def _estimate_batch(self, idx: int, comments: Sequence[CommentPayload]) -> BatchEstimates:
        config = self.estimation_config
        per_comment_tokens = [
            estimate_tokens(comment.body) + config.per_comment_prefix_tokens for comment in comments
        ]
        estimated_input_tokens = config.instructions_tokens + sum(per_comment_tokens)
        estimated_output_tokens = len(comments) * config.response_tokens_per_comment
        return BatchEstimates(
            batch_index=idx,
            comment_ids=[comment.id for comment in comments],
            comment_count=len(comments),
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        config = self.estimation_config
        input_cost = (input_tokens / 1000) * config.input_cost_per_1k
        output_cost = (output_tokens / 1000) * config.output_cost_per_1k
        return round(input_cost + output_cost, 6)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - argparse already coerces
        raise argparse.ArgumentTypeError(f"Invalid datetime: {value}") from exc


def estimate_tokens(text: str) -> int:
    cleaned = text.strip()
    if not cleaned:
        return 1
    # Rough heuristic: 1 token per 4 characters with a small buffer.
    approx = math.ceil(len(cleaned) / 4)
    return max(1, approx + 4)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.comment_llm_processing",
        description="Plan batched LLM processing for help-request comments.",
    )
    parser.add_argument("--snapshot-label", default="default", help="Label recorded with this run plan")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Comments per batch (1-25)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of comments to include")
    parser.add_argument("--min-id", type=int, help="Minimum comment ID (inclusive)")
    parser.add_argument("--max-id", type=int, help="Maximum comment ID (inclusive)")
    parser.add_argument("--resume-after-id", type=int, help="Skip comments up to and including this ID")
    parser.add_argument("--created-after", type=_parse_datetime, help="Only include comments created at or after this timestamp (ISO8601)")
    parser.add_argument("--created-before", type=_parse_datetime, help="Only include comments created at or before this timestamp (ISO8601)")
    parser.add_argument(
        "--help-request-id",
        action="append",
        type=int,
        dest="help_request_ids",
        help="Restrict processing to specific help request IDs (repeatable)",
    )
    parser.add_argument("--include-deleted", action="store_true", help="Include comments marked as deleted")
    parser.add_argument("--dry-run", action="store_true", help="Print planning information without executing batches")
    parser.add_argument("--json-summary", action="store_true", help="Emit the plan as JSON instead of text")
    parser.add_argument("--show-batches", action="store_true", help="Print a per-batch breakdown")
    parser.add_argument(
        "--instructions-tokens",
        type=int,
        default=DEFAULT_INSTRUCTIONS_TOKENS,
        help="Estimated tokens for shared instructions per batch",
    )
    parser.add_argument(
        "--per-comment-prefix-tokens",
        type=int,
        default=DEFAULT_PER_COMMENT_PREFIX_TOKENS,
        help="Estimated tokens for per-comment framing/metadata",
    )
    parser.add_argument(
        "--response-tokens-per-comment",
        type=int,
        default=DEFAULT_RESPONSE_TOKENS_PER_COMMENT,
        help="Estimated tokens returned per comment",
    )
    parser.add_argument(
        "--input-cost-per-1k",
        type=float,
        default=DEFAULT_INPUT_COST_PER_1K,
        help="Input token price in USD per 1k tokens",
    )
    parser.add_argument(
        "--output-cost-per-1k",
        type=float,
        default=DEFAULT_OUTPUT_COST_PER_1K,
        help="Output token price in USD per 1k tokens",
    )
    return parser


def _validate_batch_size(value: int) -> None:
    if not MIN_BATCH_SIZE <= value <= MAX_BATCH_SIZE:
        raise ValueError(f"Batch size must be between {MIN_BATCH_SIZE} and {MAX_BATCH_SIZE}")


def human_summary(summary: RunSummary, snapshot_label: str) -> str:
    lines = []
    lines.append(f"Snapshot: {snapshot_label}")
    lines.append(
        f"Totals: {summary.total_comments} comments across {summary.total_batches} batches (size ≤ {summary.batch_size})"
    )
    lines.append(
        f"Tokens: ~{summary.total_input_tokens:,} input / ~{summary.total_output_tokens:,} output"
    )
    lines.append(f"Estimated cost: ${summary.estimated_cost_usd:.4f}")
    filters = summary.filters
    filter_bits = []
    if filters.min_id:
        filter_bits.append(f"min_id={filters.min_id}")
    if filters.max_id:
        filter_bits.append(f"max_id={filters.max_id}")
    if filters.resume_after_id:
        filter_bits.append(f"resume_after_id={filters.resume_after_id}")
    if filters.created_after:
        filter_bits.append(f"created_after={filters.created_after.isoformat()}")
    if filters.created_before:
        filter_bits.append(f"created_before={filters.created_before.isoformat()}")
    if filters.help_request_ids:
        filter_bits.append(f"help_request_ids={','.join(map(str, filters.help_request_ids))}")
    if not filters.include_deleted:
        filter_bits.append("excluding deleted")
    lines.append("Filters: " + (", ".join(filter_bits) if filter_bits else "(none)"))
    return "\n".join(lines)


def print_batches(batches: Sequence[BatchEstimates]) -> None:
    for batch in batches:
        first = batch.comment_ids[0]
        last = batch.comment_ids[-1]
        print(
            f"Batch {batch.batch_index:03d}: {batch.comment_count} comments (IDs {first}-{last}) -> "
            f"~{batch.estimated_input_tokens} in / ~{batch.estimated_output_tokens} out tokens"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    _validate_batch_size(ns.batch_size)

    filters = SnapshotFilters(
        min_id=ns.min_id,
        max_id=ns.max_id,
        created_after=ns.created_after,
        created_before=ns.created_before,
        help_request_ids=tuple(sorted(set(ns.help_request_ids or []))),
        include_deleted=ns.include_deleted,
        resume_after_id=ns.resume_after_id,
    )
    config = EstimationConfig(
        instructions_tokens=ns.instructions_tokens,
        per_comment_prefix_tokens=ns.per_comment_prefix_tokens,
        response_tokens_per_comment=ns.response_tokens_per_comment,
        input_cost_per_1k=ns.input_cost_per_1k,
        output_cost_per_1k=ns.output_cost_per_1k,
    )

    engine = get_engine()
    with Session(engine) as session:
        planner = CommentBatchPlanner(
            session=session,
            filters=filters,
            batch_size=ns.batch_size,
            max_comments=ns.limit,
            estimation_config=config,
            snapshot_label=ns.snapshot_label,
        )
        summary = planner.plan()

    if ns.json_summary:
        payload = {
            "snapshot_label": summary.snapshot_label,
            "total_comments": summary.total_comments,
            "total_batches": summary.total_batches,
            "batch_size": summary.batch_size,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "estimated_cost_usd": summary.estimated_cost_usd,
            "filters": {
                "min_id": summary.filters.min_id,
                "max_id": summary.filters.max_id,
                "resume_after_id": summary.filters.resume_after_id,
                "created_after": summary.filters.created_after.isoformat() if summary.filters.created_after else None,
                "created_before": summary.filters.created_before.isoformat() if summary.filters.created_before else None,
                "help_request_ids": list(summary.filters.help_request_ids),
                "include_deleted": summary.filters.include_deleted,
            },
            "batches": [
                {
                    "index": batch.batch_index,
                    "comment_ids": batch.comment_ids,
                    "comment_count": batch.comment_count,
                    "estimated_input_tokens": batch.estimated_input_tokens,
                    "estimated_output_tokens": batch.estimated_output_tokens,
                }
                for batch in summary.batches
            ],
        }
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(human_summary(summary, summary.snapshot_label))
        if ns.show_batches and summary.batches:
            print("\nBatch breakdown:")
            print_batches(summary.batches)

    if summary.total_comments == 0:
        print("No comments matched the supplied filters.")
        return 0

    if ns.dry_run:
        return 0

    print("\nDry run disabled, but Stage 1 scaffolding only prints the plan. Stage 2 will execute batches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
