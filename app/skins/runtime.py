from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SkinBundle:
    name: str
    url: str
    filename: str | None
    hash: str | None


@dataclass(frozen=True)
class SkinRegistry:
    bundles: Dict[str, SkinBundle]
    manifest_found: bool


def _manifest_path(settings: Settings) -> Path:
    raw = Path(settings.skins_manifest_path)
    if raw.is_absolute():
        return raw
    return PROJECT_ROOT / raw


def _normalize_allowed(settings: Settings) -> tuple[str, ...]:
    allowed: list[str] = list(settings.skins_allowed)
    if settings.skin_default not in allowed:
        allowed.append(settings.skin_default)
    if not allowed:
        allowed.append(settings.skin_default)
    # Preserve order while removing duplicates
    seen: set[str] = set()
    deduped: list[str] = []
    for name in allowed:
        if name in seen:
            continue
        seen.add(name)
        deduped.append(name)
    return tuple(deduped)


@lru_cache(maxsize=1)
def _load_manifest(manifest_path: str) -> SkinRegistry:
    path = Path(manifest_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.info("Skin manifest not found at %s; falling back to raw skin files", path)
        return SkinRegistry(bundles={}, manifest_found=False)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid skin manifest (%s): %s", path, exc)
        return SkinRegistry(bundles={}, manifest_found=False)

    bundles: Dict[str, SkinBundle] = {}
    for name, meta in (data.get("skins") or {}).items():
        rel_path = meta.get("path") or f"static/build/skins/{meta.get('filename')}"
        if not rel_path:
            continue
        url = "/" + rel_path.lstrip("/")
        bundles[name] = SkinBundle(
            name=name,
            url=url,
            filename=meta.get("filename"),
            hash=meta.get("hash"),
        )
    return SkinRegistry(bundles=bundles, manifest_found=True)


def _resolve_bundle_url(name: str, registry: SkinRegistry) -> tuple[str, bool]:
    bundle = registry.bundles.get(name)
    if bundle:
        return bundle.url, True
    fallback = f"/static/skins/{name}.css"
    return fallback, False


def _resolve_desired_skin(request: Request, settings: Settings) -> str:
    if not settings.skins_enabled:
        return settings.skin_default

    allowed = _normalize_allowed(settings)
    desired = settings.skin_default
    if settings.skin_preview_enabled:
        override = request.query_params.get(settings.skin_preview_param)
        if override and override in allowed:
            desired = override
    return desired


def skin_bundle_href(request: Request) -> str:
    settings = get_settings()
    if not settings.skins_enabled:
        return "/static/skins/default.css"

    desired = _resolve_desired_skin(request, settings)

    manifest_path = str(_manifest_path(settings))
    registry = _load_manifest(manifest_path)
    url, found = _resolve_bundle_url(desired, registry)
    if not found:
        message = f"Skin '{desired}' missing from manifest at {manifest_path}; using {url}"
        if settings.skin_strict:
            raise RuntimeError(message)
        logger.warning(message)
    return url


def available_skins() -> dict[str, SkinBundle]:
    settings = get_settings()
    if not settings.skins_enabled:
        return {
            settings.skin_default: SkinBundle(
                name=settings.skin_default,
                url="/static/skins/default.css",
                filename=None,
                hash=None,
            )
        }
    registry = _load_manifest(str(_manifest_path(settings)))
    allowed = _normalize_allowed(settings)
    bundles: dict[str, SkinBundle] = {}
    for name in allowed:
        bundle = registry.bundles.get(name)
        if bundle:
            bundles[name] = bundle
        else:
            url = f"/static/skins/{name}.css"
            bundles[name] = SkinBundle(name=name, url=url, filename=None, hash=None)
    return bundles


def active_skin_name(request: Request) -> str:
    settings = get_settings()
    return _resolve_desired_skin(request, settings)


def register_skin_helpers(templates: Jinja2Templates) -> None:
    templates.env.globals.setdefault("skin_bundle_href", skin_bundle_href)
    templates.env.globals.setdefault("skin_active_name", active_skin_name)
