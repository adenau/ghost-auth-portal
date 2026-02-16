
# Ghost → Flask Authentication Bridge (Handoff Context)

## Current Status

The project is functional end-to-end:

- Ghost member session is fetched from `/members/api/session/`
- JWT is redirected to Flask callback via URL fragment (`#token=...`)
- Flask verifies JWT using Ghost JWKS (`RS512`, issuer, audience)
- Flask creates its own session
- Protected route returns authenticated user (confirmed with real login)

## Implemented Components

- Flask app entrypoint: `app.py`
- Reusable auth bridge package:
	- `ghost_auth_bridge/config.py`
	- `ghost_auth_bridge/jwks.py`
	- `ghost_auth_bridge/verifier.py`
	- `ghost_auth_bridge/flask_integration.py`
- Callback page template: `templates/callback.html`
- Ghost gate script (served by Flask): `static/ghost.js`
- Copy/paste Ghost HTML template: `ghost-app-login.html`
- Deployment and docs:
	- `README.md`
	- `HARDENING.md`
	- `.env.example`
	- `Procfile`

## Important Flow Details

- Ghost sign-in route must use Portal hash route: `#/portal/signin` (not `/signin/`)
- Gate page is expected at `/app-login/` on Ghost
- Flask callback route is `/auth/ghost/callback`
- Auth API route is `/api/auth/ghost`

## Security Hardening Already Done

- One-time `state` validation added across login flow
- Redirect `next` path validation (local path only)
- Session payload minimized (`sub`, `iat`, `exp`)
- Cookie security is env-configurable:
	- `SESSION_COOKIE_SECURE`
	- `SESSION_COOKIE_SAMESITE`
- Critical open-redirect token-leak risk fixed in gate scripts:
	- `r` callback target origin is validated before redirecting with token

## Local Development Notes

- Port `5000` was occupied during testing; `5001` was used successfully
- For localhost HTTP testing set:
	- `SESSION_COOKIE_SECURE=false`
- For production keep:
	- `SESSION_COOKIE_SECURE=true`

## Audit and Priorities

- Audit file: `audit.md`
- Critical issue (open redirect in gate script) is now fixed
- Remaining audit items still to address include:
	- XSS-safe rendering on index response
	- logout CSRF (GET → POST)
	- session lifetime policy
	- auth event logging
	- CSP headers

## Required Environment Variables

- `APP_SESSION_SECRET`
- `GHOST_ORIGIN` (example: `https://www.technodabbler.com`)
- `APP_CALLBACK_URL` (example: `https://test.technodabbler.com/auth/ghost/callback`)
- `JWKS_CACHE_TTL_SECONDS` (optional, default `300`)
- `SESSION_COOKIE_SECURE` (`true` in prod, `false` local HTTP)
- `SESSION_COOKIE_SAMESITE` (`Lax` default)
