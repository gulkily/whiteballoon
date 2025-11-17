#!/usr/bin/env python3
"""Update .env with any missing variables from .env.example."""
from __future__ import annotations

import argparse
from datetime import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


def parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_example(path: Path) -> List[Tuple[str, List[str], str]]:
    entries: List[Tuple[str, List[str], str]] = []
    comments: List[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            comments.append(line)
            continue
        if "=" not in stripped:
            comments.append(line)
            continue
        key, _ = stripped.split("=", 1)
        entries.append((key.strip(), comments.copy(), line))
        comments.clear()
    return entries


def ensure_env_exists(env_path: Path, example_path: Path) -> None:
    if env_path.exists():
        return
    if not example_path.exists():
        raise FileNotFoundError(f"{example_path} not found")
    shutil.copyfile(example_path, env_path)


def append_missing(env_path: Path, missing: List[Tuple[str, List[str], str]], dry_run: bool) -> None:
    if not missing:
        print("All environment variables are already present.")
        return
    print(f"Found {len(missing)} missing variables: {', '.join(key for key, _, _ in missing)}")
    if dry_run:
        print("Dry run enabled; showing additions only. No changes written.")
        for key, comments, line in missing:
            print()
            for comment in comments:
                print(comment)
            print(line)
        return
    with env_path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n# ----------------------------------------\n")
        handle.write(f"# Added automatically on {datetime.now().isoformat()}\n")
        handle.write("# ----------------------------------------\n")
        for _key, comments, line in missing:
            for comment in comments:
                handle.write(comment + "\n")
            handle.write(line + "\n")
    print(f"Appended {len(missing)} entries to {env_path}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync .env with .env.example defaults")
    parser.add_argument("--env-path", default=".env", help="Path to the .env file")
    parser.add_argument("--example-path", default=".env.example", help="Path to the example file")
    parser.add_argument("--dry-run", action="store_true", help="Show additions without writing")
    args = parser.parse_args()

    env_path = Path(args.env_path).resolve()
    example_path = Path(args.example_path).resolve()

    ensure_env_exists(env_path, example_path)

    example_entries = parse_example(example_path)
    existing_vars = parse_env_file(env_path)

    missing_entries = [(key, comments, line) for key, comments, line in example_entries if key not in existing_vars]

    append_missing(env_path, missing_entries, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
