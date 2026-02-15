from __future__ import annotations

import os
from dataclasses import dataclass


def _strip_trailing_slash(value: str) -> str:
    return value.rstrip("/")


@dataclass(frozen=True)
class GhostAuthConfig:
    app_session_secret: str
    ghost_origin: str
    app_callback_url: str
    jwks_cache_ttl_seconds: int = 300

    @property
    def jwks_url(self) -> str:
        return f"{self.ghost_origin}/members/.well-known/jwks.json"

    @property
    def expected_issuer(self) -> str:
        return f"{self.ghost_origin}/members/api"

    @property
    def expected_audience(self) -> str:
        return f"{self.ghost_origin}/members/api"

    @classmethod
    def from_env(cls) -> "GhostAuthConfig":
        missing = []
        app_session_secret = os.getenv("APP_SESSION_SECRET")
        if not app_session_secret:
            missing.append("APP_SESSION_SECRET")

        ghost_origin = os.getenv("GHOST_ORIGIN")
        if not ghost_origin:
            missing.append("GHOST_ORIGIN")

        app_callback_url = os.getenv("APP_CALLBACK_URL")
        if not app_callback_url:
            missing.append("APP_CALLBACK_URL")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            app_session_secret=app_session_secret,
            ghost_origin=_strip_trailing_slash(ghost_origin),
            app_callback_url=_strip_trailing_slash(app_callback_url),
            jwks_cache_ttl_seconds=int(os.getenv("JWKS_CACHE_TTL_SECONDS", "300")),
        )
