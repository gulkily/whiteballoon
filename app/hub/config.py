from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
from typing import Dict

from app.env import ensure_env_loaded

ensure_env_loaded()

DEFAULT_CONFIG_PATH = Path(".sync/hub_config.json")
DEFAULT_STORAGE_DIR = Path("data/hub_store")


@dataclass(frozen=True)
class HubPeer:
    name: str
    token_hash: str
    public_keys: tuple[str, ...]

    @property
    def public_key(self) -> str:
        return self.public_keys[0] if self.public_keys else ""

    def allows_public_key(self, key: str) -> bool:
        return key in self.public_keys

    def append_public_key(self, key: str) -> HubPeer:
        if key in self.public_keys:
            return self
        return HubPeer(name=self.name, token_hash=self.token_hash, public_keys=self.public_keys + (key,))


@dataclass(frozen=True)
class AdminToken:
    name: str
    token_hash: str


@dataclass(frozen=True)
class HubSettings:
    storage_dir: Path
    peers: Dict[str, HubPeer]
    token_index: Dict[str, HubPeer]
    admin_tokens: Dict[str, AdminToken]
    admin_token_index: Dict[str, AdminToken]
    allow_auto_register_push: bool = False
    allow_auto_register_pull: bool = False
    config_path: Path | None = None

    def get_peer(self, name: str) -> HubPeer | None:
        return self.peers.get(name)

    def peer_for_token_hash(self, token_hash: str) -> HubPeer | None:
        return self.token_index.get(token_hash)

    def admin_for_hash(self, token_hash: str) -> AdminToken | None:
        return self.admin_token_index.get(token_hash)

    def has_admin_tokens(self) -> bool:
        return bool(self.admin_token_index)


def hash_token(token: str) -> str:
    digest = hashlib.sha256()
    digest.update(token.encode("utf-8"))
    return digest.hexdigest()


def _normalize_keys(raw_keys: object, single_key: object, name: str) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(raw_keys, list):
        for idx, value in enumerate(raw_keys):
            if not value:
                continue
            key = str(value).strip()
            if not key:
                raise ValueError(f"Peer '{name}' has empty key at index {idx}")
            keys.append(key)
    elif raw_keys is None and single_key:
        candidate = str(single_key).strip()
        if candidate:
            keys.append(candidate)
    elif raw_keys is not None:
        raise ValueError(f"Peer '{name}' public_keys must be a list")

    if not keys:
        raise ValueError(f"Peer '{name}' missing 'public_keys' or 'public_key'")
    # Remove duplicates while preserving order
    seen: set[str] = set()
    normalized: list[str] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        normalized.append(key)
    return tuple(normalized)


def _load_peer(entry: dict) -> HubPeer:
    name = entry.get("name")
    if not name:
        raise ValueError("Peer entry missing 'name'")
    public_keys = _normalize_keys(entry.get("public_keys"), entry.get("public_key"), name)
    token_hash = entry.get("token_hash")
    token_plain = entry.get("token")
    if not token_hash and not token_plain:
        raise ValueError(f"Peer '{name}' must define 'token' or 'token_hash'")
    if not token_hash and token_plain:
        token_hash = hash_token(token_plain)
    return HubPeer(name=name, token_hash=str(token_hash), public_keys=public_keys)


def _load_settings(path: Path) -> HubSettings:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        sample = {
            "storage_dir": str(DEFAULT_STORAGE_DIR),
            "peers": [
                {
                    "name": "example",
                    "token": "replace-me",
                    "public_keys": ["BASE64PUB"],
                }
            ],
        }
        path.write_text(json.dumps(sample, indent=2) + "\n", encoding="utf-8")
        data = sample
    else:
        data = json.loads(path.read_text(encoding="utf-8"))

    storage_dir = Path(data.get("storage_dir") or DEFAULT_STORAGE_DIR)
    peers_raw = data.get("peers") or []
    if not peers_raw:
        default_peer = {
            "name": "local",
            "token": "replace-me",
            "public_keys": ["BASE64PUB"],
        }
        peers_raw = [default_peer]
        data = {
            "storage_dir": str(storage_dir),
            "peers": peers_raw,
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    peers: Dict[str, HubPeer] = {}
    token_index: Dict[str, HubPeer] = {}
    for entry in peers_raw:
        peer = _load_peer(entry)
        peers[peer.name] = peer
        token_index[peer.token_hash] = peer
    storage_dir.mkdir(parents=True, exist_ok=True)
    allow_push = bool(data.get("allow_auto_register_push", False))
    allow_pull = bool(data.get("allow_auto_register_pull", False))
    admin_tokens_raw = data.get("admin_tokens") or []
    admin_tokens: Dict[str, AdminToken] = {}
    admin_token_index: Dict[str, AdminToken] = {}
    for entry in admin_tokens_raw:
        name = entry.get("name") or "default"
        token_hash = entry.get("token_hash")
        if not token_hash:
            raise ValueError(f"Admin token '{name}' missing 'token_hash'")
        admin = AdminToken(name=str(name), token_hash=str(token_hash))
        admin_tokens[admin.name] = admin
        admin_token_index[admin.token_hash] = admin
    return HubSettings(
        storage_dir=storage_dir,
        peers=peers,
        token_index=token_index,
        admin_tokens=admin_tokens,
        admin_token_index=admin_token_index,
        allow_auto_register_push=allow_push,
        allow_auto_register_pull=allow_pull,
        config_path=path,
    )


@lru_cache()
def get_settings() -> HubSettings:
    config_path = Path(os.environ.get("WB_HUB_CONFIG", DEFAULT_CONFIG_PATH))
    return _load_settings(config_path)


def reset_settings_cache() -> None:
    get_settings.cache_clear()


__all__ = [
    "AdminToken",
    "HubPeer",
    "HubSettings",
    "get_settings",
    "reset_settings_cache",
    "hash_token",
    "persist_peer",
]

def persist_peer(config_path: Path, peer: HubPeer, *, storage_dir: Path | None = None, allow_push: bool | None = None, allow_pull: bool | None = None) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        data = {"storage_dir": str(storage_dir or DEFAULT_STORAGE_DIR), "peers": []}
    peers = data.get("peers") or []
    peers = [entry for entry in peers if entry.get("name") != peer.name]
    peers.append(
        {
            "name": peer.name,
            "token_hash": peer.token_hash,
            "public_keys": list(peer.public_keys),
            "public_key": peer.public_key,
        }
    )
    data["peers"] = peers
    if storage_dir:
        data["storage_dir"] = str(storage_dir)
    if allow_push is not None:
        data["allow_auto_register_push"] = allow_push
    if allow_pull is not None:
        data["allow_auto_register_pull"] = allow_pull
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
