from __future__ import annotations

import json
from typing import Any

import jwt
from jwt import InvalidTokenError
from jwt.algorithms import RSAAlgorithm

from .config import GhostAuthConfig
from .jwks import JwksClient


class GhostTokenError(Exception):
    pass


class GhostTokenVerifier:
    def __init__(self, config: GhostAuthConfig):
        self._config = config
        self._jwks = JwksClient(config.jwks_url, ttl_seconds=config.jwks_cache_ttl_seconds)

    def verify(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise GhostTokenError("Token header is invalid") from exc

        kid = header.get("kid")
        alg = header.get("alg")
        if not kid:
            raise GhostTokenError("Token is missing kid header")
        if alg != "RS512":
            raise GhostTokenError(f"Unexpected token algorithm: {alg}")

        jwk = self._jwks.get_key_by_kid(kid)
        if not jwk:
            raise GhostTokenError("No matching JWKS key found for token")

        try:
            public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS512"],
                audience=self._config.expected_audience,
                issuer=self._config.expected_issuer,
                options={"require": ["sub", "iss", "aud", "exp", "iat"]},
            )
        except InvalidTokenError as exc:
            raise GhostTokenError("Token verification failed") from exc

        sub = claims.get("sub")
        if not sub:
            raise GhostTokenError("Token missing required sub claim")

        return claims
