from __future__ import annotations

from fastapi import HTTPException, status
from fastapi.requests import Request

from .config import HubPeer, HubSettings, get_settings, hash_token


class AuthContext:
    def __init__(self, request: Request, settings: HubSettings | None = None) -> None:
        self.request = request
        self.settings = settings or get_settings()

    def authenticate(self, peer_name: str | None = None) -> HubPeer:
        auth = self.request.headers.get("Authorization")
        if not auth or not auth.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        token = auth.split(" ", 1)[1].strip()
        token_hash = hash_token(token)
        peer = self.settings.peer_for_token_hash(token_hash)
        if peer:
            if peer_name and peer.name != peer_name:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Token not authorized for peer '{peer_name}'",
                )
            return peer
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


__all__ = ["AuthContext"]
