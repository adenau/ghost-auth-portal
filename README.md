# Ghost → Flask Authentication Bridge

This repository contains:

- A reusable Python module to verify Ghost member JWTs in Flask
- A demo Flask app that creates its own session after Ghost verification
- A `static/ghost.js` script to embed in a Ghost page (`/app-login/`)
- A copy/paste Ghost page template in `ghost-app-login.html`

## Project Layout

- `ghost_auth_bridge/` library code
- `app.py` demo Flask resource server
- `templates/callback.html` callback page that forwards `#token` to backend
- `static/ghost.js` script for Ghost gate page
- `ghost-app-login.html` self-contained Ghost page template

## Environment Variables

Copy `.env.example` and set:

- `APP_SESSION_SECRET`
- `GHOST_ORIGIN` (example: `https://www.technodabbler.com`)
- `APP_CALLBACK_URL` (example: `https://test.technodabbler.com/auth/ghost/callback`)
- `JWKS_CACHE_TTL_SECONDS` (optional, default `300`)

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export APP_SESSION_SECRET="dev-secret"
export GHOST_ORIGIN="https://www.technodabbler.com"
export APP_CALLBACK_URL="http://localhost:5000/auth/ghost/callback"
export SESSION_COOKIE_SECURE="false"
python app.py
```

Visit `http://localhost:5000`.

## Authentication Flow

1. User visits Flask app protected route
2. If no Flask session, app redirects to Ghost `/app-login/?r=<callback_url>`
3. Ghost page loads `static/ghost.js`, calls `/members/api/session/`
4. If member session exists, Ghost redirects to Flask callback with `#token=<jwt>`
5. Callback page POSTs token to `/api/auth/ghost`
6. Flask validates one-time auth `state`, verifies JWT using Ghost JWKS, then stores Flask session

## Embed Script in Ghost (`/app-login/`)

### Option A (recommended for copy/paste): self-contained HTML

Use `ghost-app-login.html` as your source and paste its body content into a Ghost HTML card.

At minimum, update this value before publishing:

- `callbackUrl` in `window.GhostBridgeConfig`

### Option B: hosted script from Flask static

Create a Ghost page and include:

```html
<script>
  window.GhostBridgeConfig = {
    callbackUrl: "https://test.technodabbler.com/auth/ghost/callback",
    sessionEndpoint: "/members/api/session/",
    signInPath: "/portal/signin"
  };
</script>
<script src="https://test.technodabbler.com/static/ghost.js"></script>
```

## Dokku Deploy Notes

- `Procfile` is included for Dokku (`gunicorn app:app`)
- Set env vars with `dokku config:set <app> KEY=value`
- Ensure TLS is enabled and Flask callback URL uses `https`

## Security Notes

- JWT is passed via URL fragment (`#token`) and not sent to server logs by default
- JWT signature is validated with Ghost JWKS (`RS512`)
- Issuer and audience are strictly validated
- One-time `state` validation protects callback/auth API against forged login posts
- Ghost gate script validates `r` callback target origin before redirect to prevent token leakage
- Flask uses its own secure session cookie (`SESSION_COOKIE_SECURE=true` in production)
- Session stores only minimal member identity metadata (`sub`, `iat`, `exp`)

## Deployment Hardening

Use the production checklist in `HARDENING.md`.
