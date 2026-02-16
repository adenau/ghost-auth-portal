from __future__ import annotations

import os
from datetime import timedelta

from flask import Flask, jsonify, session
from markupsafe import escape

from ghost_auth_bridge import GhostAuthConfig, create_ghost_auth_blueprint, ghost_login_required


def create_app() -> Flask:
    app = Flask(__name__)
    config = GhostAuthConfig.from_env()

    session_cookie_secure = os.getenv("SESSION_COOKIE_SECURE", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    app.secret_key = config.app_session_secret
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=session_cookie_samesite,
        SESSION_COOKIE_SECURE=session_cookie_secure,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
        GHOST_AUTH_CONFIG=config,
    )

    app.register_blueprint(create_ghost_auth_blueprint(config))

    @app.get("/")
    @ghost_login_required
    def index() -> str:
        return f'''
        <html>
        <body>
            <h1>Hello, {escape(session['ghost_sub'])}!</h1>
            <form method="post" action="/logout">
                <button type="submit">Logout</button>
            </form>
        </body>
        </html>
        '''

    @app.get("/api/me")
    @ghost_login_required
    def me():
        return jsonify(
            {
                "sub": session.get("ghost_sub"),
                "iat": session.get("ghost_iat"),
                "exp": session.get("ghost_exp"),
            }
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True})

    return app


app = create_app()


if __name__ == "__main__":
    print(app.url_map)
    app.run(host="0.0.0.0", port=5002, debug=True)
