# Production Hardening Checklist

Use this checklist before exposing the bridge in production.

## 1) Secrets and Configuration

- [ ] Set a strong `APP_SESSION_SECRET` (32+ random bytes) and store it in server secrets, not git.
- [ ] Set `GHOST_ORIGIN` and `APP_CALLBACK_URL` to final HTTPS production values.
- [ ] Keep `SESSION_COOKIE_SECURE=true` in production.
- [ ] Keep `SESSION_COOKIE_SAMESITE=Lax` unless you have a strict reason to change it.
- [ ] Set `JWKS_CACHE_TTL_SECONDS` to a reasonable value (e.g. 300).

## 2) Flask Runtime and Proxy

- [ ] Run behind `gunicorn` (already in `Procfile`) and not Flask dev server.
- [ ] Ensure TLS terminates before Flask (Cloudflare / reverse proxy).
- [ ] Preserve and trust forwarded headers correctly at your edge/proxy.
- [ ] Restrict direct origin access (only tunnel/proxy should reach app).

## 3) Auth Flow Safety

- [ ] Keep state validation enabled (already implemented in callback flow).
- [ ] Ensure callback is always HTTPS in production.
- [ ] Keep redirect target validation strict (only local paths in app redirect).
- [ ] Avoid storing full JWTs/claims in session cookies (already minimized).

## 4) Network Controls

- [ ] Restrict inbound traffic to only required ports/services.
- [ ] If using Cloudflare Tunnel, limit exposure to known hostnames/routes.
- [ ] Add rate limiting on auth endpoints (`/api/auth/ghost`, callback route) at edge or app.

## 5) Logging and Monitoring

- [ ] Log auth success/failure events with non-sensitive metadata only.
- [ ] Never log raw JWT tokens.
- [ ] Add alerts for spikes in `Invalid authentication state` or token verification failures.
- [ ] Keep log retention and access controls aligned with your policy.

## 6) Dependency and Patch Hygiene

- [ ] Pin dependencies and update regularly.
- [ ] Monitor CVEs for Flask, PyJWT, cryptography, requests, gunicorn.
- [ ] Rebuild/redeploy quickly for critical security patches.

## 7) Ghost-Side Controls

- [ ] Keep Ghost updated to current security release.
- [ ] Verify `/members/api/session/` behavior after Ghost upgrades.
- [ ] Verify Portal sign-in route on your theme (`#/portal/signin`) still works.

## 8) Operational Readiness

- [ ] Add a simple runbook for auth incidents (login loop, invalid state, key fetch errors).
- [ ] Document rollback plan (previous container/image + config).
- [ ] Test restart/redeploy while active sessions exist.

## 9) Quick Smoke Test After Deploy

- [ ] Open protected route while logged out; confirm redirect to Ghost login flow.
- [ ] Log in via Ghost; confirm callback succeeds and app session is created.
- [ ] Refresh protected route; confirm session persists.
- [ ] Hit `/logout`; confirm app session is cleared.
