from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKINS_DIR = PROJECT_ROOT / "static" / "skins"
BASE_FILENAME = "base.css"
BUILD_DIR = PROJECT_ROOT / "static" / "build" / "skins"
MANIFEST_FILENAME = "manifest.json"
IMPORT_BASE_PATTERN = re.compile(r"@import\s+url\(\"\.\/base\.css\"\);?\s*", re.IGNORECASE)


@dataclass(slots=True)
class SkinEntry:
    name: str
    path: Path


class SkinBuildError(RuntimeError):
    """Raised when skins cannot be built."""


def discover_skins(directory: Path | None = None) -> list[SkinEntry]:
    directory = directory or SKINS_DIR
    if not directory.exists():
        raise SkinBuildError(f"Skins directory missing: {directory}")
    entries: list[SkinEntry] = []
    for css_file in sorted(directory.glob("*.css")):
        if css_file.name == BASE_FILENAME:
            continue
        entries.append(SkinEntry(name=css_file.stem, path=css_file))
    if not entries:
        raise SkinBuildError("No skin entry files found. Create at least one skin (e.g., default.css).")
    return entries


def _load_base_css(base_path: Path | None = None) -> str:
    path = base_path or (SKINS_DIR / BASE_FILENAME)
    if not path.exists():
        raise SkinBuildError(f"Base stylesheet not found: {path}")
    return path.read_text(encoding="utf-8")


def _strip_base_import(css: str) -> str:
    return IMPORT_BASE_PATTERN.sub("", css, count=1)


def _compose_bundle(base_css: str, skin_css: str, skin_name: str) -> str:
    combined = base_css
    if not combined.endswith("\n"):
        combined += "\n"
    skin_body = _strip_base_import(skin_css).lstrip()
    combined += f"\n/* --- Skin overrides: {skin_name} --- */\n"
    combined += skin_body
    if not combined.endswith("\n"):
        combined += "\n"
    return combined


def _hashed_filename(skin_name: str, content: str) -> tuple[str, str]:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:10]
    filename = f"skin-{skin_name}.{digest}.css"
    return filename, digest


def _cleanup_old_outputs(output_dir: Path, skin_name: str, keep_filename: str) -> None:
    pattern = f"skin-{skin_name}.*.css"
    for existing in output_dir.glob(pattern):
        if existing.name != keep_filename:
            try:
                existing.unlink()
            except OSError:
                pass


def build_skins(
    *,
    skins: Iterable[SkinEntry] | None = None,
    base_css_path: Path | None = None,
    output_dir: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, dict[str, str]]:
    base_css = _load_base_css(base_css_path)
    entries = list(skins) if skins is not None else discover_skins()
    output_dir = output_dir or BUILD_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, str]] = {}

    for entry in entries:
        skin_css = entry.path.read_text(encoding="utf-8")
        bundle = _compose_bundle(base_css, skin_css, entry.name)
        filename, digest = _hashed_filename(entry.name, bundle)
        target_path = output_dir / filename
        target_path.write_text(bundle, encoding="utf-8")
        _cleanup_old_outputs(output_dir, entry.name, filename)
        manifest[entry.name] = {
            "filename": filename,
            "hash": digest,
            "path": str(target_path.relative_to(PROJECT_ROOT)),
        }

    manifest_path = manifest_path or (output_dir / MANIFEST_FILENAME)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_payload = {
        "generated_at": int(time.time()),
        "skins": manifest,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")
    return manifest


def watch_skins(
    *,
    interval: float = 1.0,
    base_css_path: Path | None = None,
    output_dir: Path | None = None,
    manifest_path: Path | None = None,
    log: Callable[[str], None] | None = None,
) -> None:
    log = log or (lambda msg: None)
    base_path = base_css_path or (SKINS_DIR / BASE_FILENAME)

    def snapshot() -> dict[Path, float]:
        files = [base_path, *[entry.path for entry in discover_skins()]]
        state: dict[Path, float] = {}
        for file_path in files:
            try:
                state[file_path] = file_path.stat().st_mtime_ns
            except FileNotFoundError:
                state[file_path] = -1
        return state

    previous_state = snapshot()
    log("Initial build...")
    build_skins(base_css_path=base_path, output_dir=output_dir, manifest_path=manifest_path)

    try:
        while True:
            time.sleep(interval)
            try:
                current_state = snapshot()
            except SkinBuildError as exc:
                log(f"[skins] {exc}")
                continue
            if current_state != previous_state:
                log("Changes detected. Rebuilding skins...")
                build_skins(base_css_path=base_path, output_dir=output_dir, manifest_path=manifest_path)
                previous_state = current_state
    except KeyboardInterrupt:
        log("Stopping skin watcher")
