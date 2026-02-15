
# Ghost → Flask Authentication Bridge


## Overview

The goal of this project is to create a python library that I can integrate in my applications so that I can leverage Ghost Blog authentification into my web application. In that sense, I'm using Ghost blog kinda like a SSO and my members never need to sign up to something new. 

Ghost acts as the **identity provider**.  
The Flask app acts as the **resource server**.

Authentication is handled via Ghost-issued JWT tokens, which are verified server-side in Flask using Ghost’s public keys.

---

## Goals

- Use Ghost Members for signup and login
- Avoid duplicating authentication logic
- Avoid sharing cookies across domains
- Keep the Flask app non-publicly exposed
- Include a test application that can be deploy using Dokku on a VPS
- Have the javascript code I need to embed in a Ghost page in ghost.js

---

## Architecture

### 1. Ghost (Identity Provider)


Provides:

- Member login
- Session JWT via `/members/api/session/`
- Public key set via `/members/.well-known/jwks.json`

---

### 2. Flask Application (Protected Resource)`

Responsibilities:

- Receives Ghost JWT
- Verifies signature using JWKS
- Validates issuer and audience
- Creates Flask session
- Protects application routes

---

## Authentication Flow

Using the following URL as test URLs

### Step 1 — User Accesses Flask App

User visits:

https://test.technodabbler.com

perl
Copy code

If no Flask session exists:

Redirect to:

https://www.technodabbler.com/app-login/?r=https://test.technodabbler.com/auth/ghost/callback

yaml
Copy code

---

### Step 2 — Ghost Gate Page

The `/app-login/` page:

- Calls `/members/api/session/`
- If response is `204` → user not logged in → redirect to Ghost sign-in
- If JWT returned → redirect to Flask:

https://test.technodabbler.com/auth/ghost/callback#token=<jwt>

yaml
Copy code

---

### Step 3 — Flask Callback

Route: `/auth/ghost/callback`

- Extracts JWT from URL fragment
- Sends token via POST to `/api/auth/ghost`

---

### Step 4 — Token Verification (Server-Side)

Flask:

1. Fetches JWKS from:

https://www.technodabbler.com/members/.well-known/jwks.json

yaml
Copy code

2. Verifies JWT:
- Algorithm: `RS512`
- Audience: `https://www.technodabbler.com/members/api`
- Issuer: `https://www.technodabbler.com/members/api`

3. Extracts:
- `sub` (email)

4. Creates Flask session

---

### Step 5 — Authenticated Access

User is redirected to `/`.

Flask session now exists.

Protected routes are accessible.

---

## Security Model

- JWT passed via URL fragment (`#token=`)
- Fragment is not sent to server logs
- No cross-domain cookie sharing
- Flask sets its own secure session cookie
- JWT signature verified using Ghost public keys
- App is not publicly exposed (Cloudflare Tunnel only)

---

## Required Environment Variables

APP_SESSION_SECRET
GHOST_ORIGIN=https://www.technodabbler.com
APP_CALLBACK_URL=https://test.technodabbler.com/auth/ghost/callback
---

## Development Mode

For local testing:

- Flask runs on `http://localhost:5000`
- Ghost gate page may temporarily redirect to localhost
- JWT verification logic remains identical

---

## Future Improvements

- Enforce Ghost paid tiers
- Role-based authorization
- Nonce/state validation
- Logout synchronization
- Replace Flask session with signed internal JWT
- Centralized auth microservice
- Automated deployment script
- Admin interface
