from __future__ import annotations

from pathlib import Path

from app.sync.peers import Peer, get_peer, load_peers, save_peers


def test_peer_file_round_trip(tmp_path: Path) -> None:
    peer_file = tmp_path / "sync_peers.txt"
    peers = [Peer(name="hub", path=Path("data/hub"), token="secret", public_key="ZmFrZQ==")]
    save_peers(peers, peer_file)

    loaded = load_peers(peer_file)
    assert len(loaded) == 1
    assert loaded[0].name == "hub"
    assert loaded[0].path == Path("data/hub")
    assert loaded[0].token == "secret"
    assert loaded[0].public_key == "ZmFrZQ=="

    peer = get_peer("hub", peer_file)
    assert peer is not None
    assert peer.name == "hub"
