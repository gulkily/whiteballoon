#!/usr/bin/env python3
"""Utility script for Dedalus log maintenance."""
from __future__ import annotations

import argparse

from app.env import ensure_env_loaded
from app import config
from app.dedalus import log_store


def purge_logs(days: int) -> int:
    ensure_env_loaded()
    removed = log_store.purge_older_than_days(days)
    print(f"Removed {removed} Dedalus runs older than {days} days")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dedalus log maintenance helper")
    subparsers = parser.add_subparsers(dest="command")

    purge_parser = subparsers.add_parser("purge", help="Delete log entries older than retention")
    purge_parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override retention window (defaults to DEDALUS_LOG_RETENTION_DAYS)",
    )

    args = parser.parse_args()
    if args.command == "purge":
        settings = config.get_settings()
        days = args.days if args.days is not None else settings.dedalus_log_retention_days
        return purge_logs(days)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
