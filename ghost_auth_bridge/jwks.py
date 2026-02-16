from __future__ import annotations

import time
from typing import Any

import requests
from requests import RequestException


class JwksClient:
    def __init__(self, jwks_url: str, ttl_seconds: int = 300, timeout_seconds: int = 5) -> None:
        self._jwks_url = jwks_url
        self._ttl_seconds = ttl_seconds
        self._timeout_seconds = timeout_seconds
        self._cached_jwks: dict[str, Any] | None = None
        self._cache_until = 0.0

    def get_jwks(self, force_refresh: bool = False) -> dict[str, Any]:
        now = time.time()
        if not force_refresh and self._cached_jwks and now < self._cache_until:
            return self._cached_jwks

        try:
            response = requests.get(self._jwks_url, timeout=self._timeout_seconds)
            response.raise_for_status()
        except RequestException as exc:
            if self._cached_jwks:
                # Use stale cache if we have it
                return self._cached_jwks
            raise ValueError(f"Unable to fetch JWKS from {self._jwks_url}: {exc}") from exc

        payload = response.json()

        if "keys" not in payload or not isinstance(payload["keys"], list):
            raise ValueError("Invalid JWKS response: missing keys list")

        self._cached_jwks = payload
        self._cache_until = now + self._ttl_seconds
        return payload

    def get_key_by_kid(self, kid: str) -> dict[str, Any] | None:
        jwks = self.get_jwks()
        for key in jwks["keys"]:
            if key.get("kid") == kid:
                return key

        jwks = self.get_jwks(force_refresh=True)
        for key in jwks["keys"]:
            if key.get("kid") == kid:
                return key
        return None
