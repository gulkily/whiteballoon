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
        raise FileNotFoundError(
            f"Hub config not found. A sample file was created at {path}. Fill it out and restart."
        )

    data = json.loads(path.read_text(encoding="utf-8"))
    storage_dir = Path(data.get("storage_dir") or DEFAULT_STORAGE_DIR)
    peers_raw = data.get("peers") or []
    peers: Dict[str, HubPeer] = {}
    token_index: Dict[str, HubPeer] = {}
    for entry in peers_raw:
        peer = _load_peer(entry)
        peers[peer.name] = peer
        token_index[peer.token_hash] = peer
    storage_dir.mkdir(parents=True, exist_ok=True)
    return HubSettings(storage_dir=storage_dir, peers=peers, token_index=token_index)


@lru_cache()
def get_settings() -> HubSettings:
    config_path = Path(os.environ.get("WB_HUB_CONFIG", DEFAULT_CONFIG_PATH))
    return _load_settings(config_path)


def reset_settings_cache() -> None:
    get_settings.cache_clear()


__all__ = ["HubPeer", "HubSettings", "get_settings", "reset_settings_cache", "hash_token"]
