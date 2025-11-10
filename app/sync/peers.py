from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PEER_FILE = Path(".sync/sync_peers.txt")


@dataclass
class Peer:
    name: str
    path: Path
    token: str | None = None
    public_key: str | None = None


def load_peers(peer_file: Path | None = None) -> list[Peer]:
    file_path = peer_file or PEER_FILE
    if not file_path.exists():
        return []
    peers: list[Peer] = []
    current: dict[str, str] | None = None
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            if current:
                peers.append(_peer_from_dict(current))
            current = {}
            continue
        if "=" in line and current is not None:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip()
    if current:
        peers.append(_peer_from_dict(current))
    return peers


def save_peers(peers: Iterable[Peer], peer_file: Path | None = None) -> None:
    file_path = peer_file or PEER_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for peer in peers:
        lines.append("[peer]")
        lines.append(f"name={peer.name}")
        lines.append(f"path={peer.path}")
        if peer.token:
            lines.append(f"token={peer.token}")
        if peer.public_key:
            lines.append(f"public_key={peer.public_key}")
        lines.append("")
    file_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def get_peer(name: str, peer_file: Path | None = None) -> Peer | None:
    peers = load_peers(peer_file)
    for peer in peers:
        if peer.name == name:
            return peer
    return None


def _peer_from_dict(data: dict[str, str]) -> Peer:
    name = data.get("name")
    path = data.get("path")
    if not name or not path:
        raise ValueError("Peer entries require name and path")
    return Peer(name=name, path=Path(path), token=data.get("token"), public_key=data.get("public_key"))
