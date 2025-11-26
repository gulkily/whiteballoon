from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Iterable, Optional

from app.services import comment_llm_insights_db


@dataclass
class CommentInsight:
    comment_id: int
    help_request_id: int
    run_id: str
    summary: str
    resource_tags: list[str]
    request_tags: list[str]
    audience: str
    residency_stage: str
    location: str
    location_precision: str
    urgency: str
    sentiment: str
    tags: list[str]
    notes: str
    recorded_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class RunSummary:
    run_id: str
    snapshot_label: str
    provider: str
    model: str
    started_at: str
    completed_batches: int
    total_batches: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _decode_list(payload: str | None) -> list[str]:
    if not payload:
        return []
    try:
        value = json.loads(payload)
        if isinstance(value, list):
            return [str(item) for item in value if isinstance(item, str)]
    except json.JSONDecodeError:
        pass
    parts = [part.strip() for part in payload.split(",") if part.strip()]
    return parts


def get_analysis_by_comment_id(comment_id: int) -> Optional[CommentInsight]:
    with comment_llm_insights_db.open_connection() as conn:
        row = conn.execute(
            """
            SELECT comment_id, help_request_id, run_id, summary, resource_tags, request_tags,
                   audience, residency_stage, location, location_precision, urgency,
                   sentiment, tags, notes, recorded_at
            FROM comment_llm_analyses
            WHERE comment_id = ?
            """,
            (comment_id,),
        ).fetchone()
    if not row:
        return None
    (
        cid,
        help_request_id,
        run_id,
        summary,
        resource_tags,
        request_tags,
        audience,
        residency_stage,
        location,
        location_precision,
        urgency,
        sentiment,
        tags,
        notes,
        recorded_at,
    ) = row
    return CommentInsight(
        comment_id=cid,
        help_request_id=help_request_id,
        run_id=run_id,
        summary=summary or "",
        resource_tags=_decode_list(resource_tags),
        request_tags=_decode_list(request_tags),
        audience=audience or "",
        residency_stage=residency_stage or "",
        location=location or "",
        location_precision=location_precision or "",
        urgency=urgency or "",
        sentiment=sentiment or "",
        tags=_decode_list(tags),
        notes=notes or "",
        recorded_at=recorded_at,
    )


def list_recent_runs(limit: int = 20) -> list[RunSummary]:
    with comment_llm_insights_db.open_connection() as conn:
        rows = conn.execute(
            """
            SELECT run_id, snapshot_label, provider, model, started_at, completed_batches, total_batches
            FROM comment_llm_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    summaries = [
        RunSummary(
            run_id=row[0],
            snapshot_label=row[1],
            provider=row[2],
            model=row[3],
            started_at=row[4],
            completed_batches=row[5],
            total_batches=row[6],
        )
        for row in rows
    ]
    return summaries


def list_analyses_for_run(run_id: str, limit: int = 200) -> list[CommentInsight]:
    with comment_llm_insights_db.open_connection() as conn:
        rows = conn.execute(
            """
            SELECT comment_id, help_request_id, run_id, summary, resource_tags, request_tags,
                   audience, residency_stage, location, location_precision, urgency,
                   sentiment, tags, notes, recorded_at
            FROM comment_llm_analyses
            WHERE run_id = ?
            ORDER BY recorded_at ASC
            LIMIT ?
            """,
            (run_id, limit),
        ).fetchall()
    return [
        CommentInsight(
            comment_id=row[0],
            help_request_id=row[1],
            run_id=row[2],
            summary=row[3] or "",
            resource_tags=_decode_list(row[4]),
            request_tags=_decode_list(row[5]),
            audience=row[6] or "",
            residency_stage=row[7] or "",
            location=row[8] or "",
            location_precision=row[9] or "",
            urgency=row[10] or "",
            sentiment=row[11] or "",
            tags=_decode_list(row[12]),
            notes=row[13] or "",
            recorded_at=row[14],
        )
        for row in rows
    ]
