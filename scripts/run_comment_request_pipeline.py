#!/usr/bin/env python3
"""
Orchestrate the end-to-end comment/request processing pipeline.

Runs chat indexing, embeddings, comment LLM analyses, and promotion workers
in the correct order so newly added requests/comments are processed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.tools import comment_llm_processing

WB_ENTRY = REPO_ROOT / "wb.py"
WB_BASE = [sys.executable, str(WB_ENTRY)] if WB_ENTRY.exists() else ["./wb"]
DEFAULT_LOCAL_EMBED_DIM = 384


def _timestamp_label(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"


def _run(name: str, args: Sequence[str], *, dry_run: bool) -> None:
    printable = " ".join(args)
    print(f"[pipeline] {name}: {printable}")
    if dry_run:
        return
    subprocess.run(args, cwd=REPO_ROOT, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run chat indexing, embeddings, comment insights, and promotion queues in order."
    )
    parser.add_argument(
        "--snapshot-label",
        help="Optional label for the comment-LLM run (defaults to pipeline-<UTC timestamp>).",
    )
    parser.add_argument(
        "--embedding-adapter",
        choices=("dedalus", "local"),
        default="dedalus",
        help="Embedding provider for chat embeddings (default: %(default)s).",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-3-large",
        help="Embedding model alias (Dedalus adapter only).",
    )
    parser.add_argument(
        "--embedding-dimensions",
        type=int,
        default=DEFAULT_LOCAL_EMBED_DIM,
        help="Local adapter vector dimensions (default: %(default)s).",
    )
    parser.add_argument(
        "--embedding-max-comments",
        type=int,
        default=40,
        help="Newest N comments per request to embed (default: %(default)s).",
    )
    parser.add_argument(
        "--comment-provider",
        choices=("dedalus", "mock"),
        default="dedalus",
        help="LLM backend for comment analyses (default: %(default)s).",
    )
    parser.add_argument(
        "--comment-model",
        default=comment_llm_processing.DEFAULT_MODEL,
        help="LLM model alias for comment analyses.",
    )
    parser.add_argument(
        "--comment-batch-size",
        type=int,
        default=comment_llm_processing.DEFAULT_BATCH_SIZE,
        help="Comments per LLM batch (default: %(default)s).",
    )
    parser.add_argument(
        "--comment-limit",
        type=int,
        help="Optional cap on the number of comments to analyze.",
    )
    parser.add_argument(
        "--comment-max-spend-usd",
        type=float,
        help="Stops execution if the estimated spend would exceed this amount.",
    )
    parser.add_argument(
        "--promotion-limit",
        type=int,
        default=200,
        help="Maximum queued promotion entries to process (default: %(default)s).",
    )
    parser.add_argument("--skip-chat-index", action="store_true", help="Skip the chat indexing step.")
    parser.add_argument("--skip-chat-embed", action="store_true", help="Skip the chat embedding step.")
    parser.add_argument("--skip-comment-llm", action="store_true", help="Skip the comment LLM step.")
    parser.add_argument("--skip-promotions", action="store_true", help="Skip promotion processing.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    label = args.snapshot_label or _timestamp_label("pipeline")
    chat_index_cmd = WB_BASE + ["chat-index", "--all"]
    chat_embed_cmd = (
        WB_BASE
        + [
            "chat-embed",
            "--all",
            "--max-comments",
            str(args.embedding_max_comments),
            "--adapter",
            args.embedding_adapter,
            "--force",
        ]
    )
    if args.embedding_adapter == "dedalus":
        chat_embed_cmd += ["--model", args.embedding_model]
    else:
        chat_embed_cmd += ["--dimensions", str(args.embedding_dimensions)]

    comment_cmd = (
        WB_BASE
        + [
            "comment-llm",
            "--snapshot-label",
            label,
            "--batch-size",
            str(args.comment_batch_size),
            "--provider",
            args.comment_provider,
            "--model",
            args.comment_model,
            "--execute",
        ]
    )
    if args.comment_limit:
        comment_cmd += ["--limit", str(args.comment_limit)]
    if args.comment_max_spend_usd:
        comment_cmd += ["--max-spend-usd", f"{args.comment_max_spend_usd}"]

    promotion_cmd = WB_BASE + [
        "promote-comment-batch",
        "run",
        "--limit",
        str(args.promotion_limit),
    ]

    try:
        if not args.skip_chat_index:
            _run("chat-index", chat_index_cmd, dry_run=args.dry_run)
        if not args.skip_chat_embed:
            _run("chat-embed", chat_embed_cmd, dry_run=args.dry_run)
        if not args.skip_comment_llm:
            _run("comment-llm", comment_cmd, dry_run=args.dry_run)
        if not args.skip_promotions:
            _run("promote-comment-batch", promotion_cmd, dry_run=args.dry_run)
    except subprocess.CalledProcessError as exc:
        print(f"[pipeline] Step failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    except KeyboardInterrupt:
        print("\n[pipeline] Interrupted; aborting remaining steps.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
