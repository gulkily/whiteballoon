from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
from typing import Dict

DEFAULT_CONFIG_PATH = Path(".sync/hub_config.json")
DEFAULT_STORAGE_DIR = Path("data/hub_store")


@dataclass(frozen=True)
class HubPeer:
    name: str
    token_hash: str
    public_key: str


@dataclass(frozen=True)
class HubSettings:
    storage_dir: Path
    peers: Dict[str, HubPeer]
    token_index: Dict[str, HubPeer]
    allow_auto_register_push: bool = False
    allow_auto_register_pull: bool = False
    config_path: Path | None = None

    def get_peer(self, name: str) -> HubPeer | None:
        return self.peers.get(name)

    def peer_for_token_hash(self, token_hash: str) -> HubPeer | None:
        return self.token_index.get(token_hash)


def hash_token(token: str) -> str:
    digest = hashlib.sha256()
    digest.update(token.encode("utf-8"))
    return digest.hexdigest()


def _load_peer(entry: dict) -> HubPeer:
    name = entry.get("name")
    if not name:
        raise ValueError("Peer entry missing 'name'")
    public_key = entry.get("public_key")
    if not public_key:
        raise ValueError(f"Peer '{name}' missing 'public_key'")
    token_hash = entry.get("token_hash")
    token_plain = entry.get("token")
    if not token_hash and not token_plain:
        raise ValueError(f"Peer '{name}' must define 'token' or 'token_hash'")
    if not token_hash and token_plain:
        token_hash = hash_token(token_plain)
    return HubPeer(name=name, token_hash=str(token_hash), public_key=str(public_key))


def _load_settings(path: Path) -> HubSettings:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        sample = {
            "storage_dir": str(DEFAULT_STORAGE_DIR),
            "peers": [
                {
                    "name": "example",
                    "token": "replace-me",
                    "public_key": "BASE64PUB",
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
            "public_key": "BASE64PUB",
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
    return HubSettings(
        storage_dir=storage_dir,
        peers=peers,
        token_index=token_index,
        allow_auto_register_push=allow_push,
        allow_auto_register_pull=allow_pull,
    )


@lru_cache()
def get_settings() -> HubSettings:
    config_path = Path(os.environ.get("WB_HUB_CONFIG", DEFAULT_CONFIG_PATH))
    return _load_settings(config_path)


def reset_settings_cache() -> None:
    get_settings.cache_clear()


__all__ = ["HubPeer", "HubSettings", "get_settings", "reset_settings_cache", "hash_token", "persist_peer"]

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
