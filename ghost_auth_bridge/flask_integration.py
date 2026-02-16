from __future__ import annotations

import logging
import secrets
from functools import wraps
from typing import Any, Callable
from urllib.parse import quote, urlencode, urlsplit

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, request, session

from .config import GhostAuthConfig
from .verifier import GhostTokenError, GhostTokenVerifier

logger = logging.getLogger(__name__)


def ghost_login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if "ghost_sub" not in session:
            config = current_app.config["GHOST_AUTH_CONFIG"]
            requested_path = request.full_path if request.query_string else request.path
            state = secrets.token_urlsafe(24)
            session["ghost_auth_state"] = state
            callback_with_next = f"{config.app_callback_url}?{urlencode({'next': requested_path, 'state': state})}"
            gate_url = f"{config.ghost_origin}/app-login/?r={quote(callback_with_next, safe=':/%')}"
            return redirect(gate_url)
        return view(*args, **kwargs)

    return wrapped


def create_ghost_auth_blueprint(config: GhostAuthConfig) -> Blueprint:
    bp = Blueprint("ghost_auth", __name__, template_folder="../templates")
    verifier = GhostTokenVerifier(config)

    @bp.get("/auth/ghost/callback")
    def ghost_callback() -> str:
        next_path = request.args.get("next", "/")
        state = request.args.get("state", "")
        return render_template("callback.html", next_path=next_path, state=state)

    @bp.post("/api/auth/ghost")
    def ghost_api_auth() -> Response:
        payload = request.get_json(silent=True) or {}
        token = payload.get("token")
        state = payload.get("state")
        next_path = payload.get("next") or "/"
        parsed_next = urlsplit(next_path)
        if parsed_next.scheme or parsed_next.netloc or not next_path.startswith("/"):
            next_path = "/"

        expected_state = session.get("ghost_auth_state")
        if not state or not isinstance(state, str) or not expected_state or state != expected_state:
            logger.warning("Invalid authentication state", extra={
                "has_state": bool(state),
                "has_expected_state": bool(expected_state),
                "user_agent": request.headers.get("User-Agent", "unknown")[:100]
            })
            return jsonify({"ok": False, "error": "Invalid authentication state"}), 400
        session.pop("ghost_auth_state", None)

        if not token or not isinstance(token, str):
            return jsonify({"ok": False, "error": "Missing token"}), 400

        try:
            claims = verifier.verify(token)
            logger.info("Ghost authentication successful", extra={
                "sub": claims["sub"], 
                "iat": claims.get("iat"),
                "user_agent": request.headers.get("User-Agent", "unknown")[:100]
            })
        except GhostTokenError as exc:
            logger.warning("Ghost token verification failed", extra={
                "error": str(exc),
                "user_agent": request.headers.get("User-Agent", "unknown")[:100]
            })
            return jsonify({"ok": False, "error": str(exc)}), 401
        except Exception as exc:
            logger.error("Ghost token verification error", extra={
                "error": str(exc),
                "error_type": type(exc).__name__
            })
            return jsonify({"ok": False, "error": "Authentication service temporarily unavailable"}), 503

        session["ghost_sub"] = claims["sub"]
        session["ghost_iat"] = claims.get("iat")
        session["ghost_exp"] = claims.get("exp")
        session.permanent = True
        return jsonify({"ok": True, "redirect": next_path})

    @bp.post("/logout")
    def logout() -> Response:
        session.clear()
        return redirect("/")

    return bp
