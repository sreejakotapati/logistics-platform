# Security Hardening (Sprint 2 — S2-T8)

This document describes the security controls added in S2-T8 and the principles that constrain them. The
controls layer onto the existing auth, Redis, and audit subsystems without changing any API contract and
without weakening any control that was already in place.

## Principles

Four rules governed every decision here. **No breaking API changes** — request and response shapes are
untouched; the only new endpoints are additive. **No weakening of existing controls** — password
verification, refresh-token rotation/reuse detection, and Postgres RLS are never bypassed by any new code
path. **Everything auditable** — each security decision writes a `security.*` event to the existing
`audit_logs`. **Everything configurable** — every threshold, window, and toggle lives in `Settings` with a
safe default.

A recurring consequence of "no weakening" is the **fail-open** posture of the Redis-backed controls (rate
limiting, lockout, abuse monitoring). If Redis is unreachable, those controls are skipped rather than
blocking traffic — but the request still has to pass password verification, token rotation, and RLS, so the
security baseline is intact. Conversely, the controls never *replace* the baseline; they sit in front of it.

No database migration was required: security events reuse `audit_logs`; rate-limit, lockout, and abuse
state live in Redis; session management reads the existing `auth_refresh_tokens` rows.

## Controls

### Rate limiting

A Redis fixed-window limiter (`RateLimiter`) keyed per client IP. `RateLimitMiddleware` applies a generous
global limit to every request and a tighter limit to authentication POSTs under `/api/v1/auth`. A blocked
request returns `429` in the standard error envelope (`code: "rate_limited"`) with `Retry-After`,
`RateLimit-Limit`, and `RateLimit-Remaining` headers; successful requests carry `RateLimit-Remaining`.
Health and docs paths and CORS preflight (`OPTIONS`) are skipped. Client IP honours the first
`X-Forwarded-For` hop when present.

### Account lockout and login-abuse protection

`LoginGuard` tracks failed logins per account and per IP in Redis. After `login_max_failures` within the
failure window, the account is locked for `login_lockout_seconds`. Crucially, a locked login returns the
**same generic `401`** as a wrong password — lockout does not reveal whether an account exists, preserving
the codebase's existing no-enumeration posture. The per-IP failure counter feeds distributed brute-force
detection. The login route checks the lock first, records failures on `UnauthorizedError`, and clears the
counter on success.

### Password policy

`PasswordPolicy` enforces minimum/maximum length, a minimum number of character classes (of lowercase,
uppercase, digit, symbol), and a common-password deny-list. It runs in `register`, `provision` (when a
password is supplied), and `confirm_password_reset`. It only ever strengthens validation — the Pydantic
`min_length` still applies first — and raises `422` with `code: "weak_password"`. The current rules are
readable by clients at `GET /api/v1/security/policy`.

### Session management

A session is a refresh-token family. `SessionService` lists a user's active families, revokes a specific
family, and revokes all families except the current one; `enforce_max_concurrent` caps concurrent sessions
and evicts the oldest beyond the cap at login. The current session is identified from the request's refresh
cookie — which is why these endpoints live under `/auth` (the cookie is scoped to `/api/v1/auth`, so it is
never sent to unrelated paths). Every revocation is audited.

### Security headers

`SecurityHeadersMiddleware` adds `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`, `Cross-Origin-Opener-Policy`, `X-Permitted-Cross-Domain-Policies`, and a
`Content-Security-Policy` to every response. CSP is skipped for the API docs (Swagger needs a CDN). HSTS is
emitted only in production. All header values are configurable.

### CSRF protection

The refresh token is an httpOnly cookie, so it is an ambient credential and therefore the CSRF vector.
`CsrfMiddleware` verifies the `Origin`/`Referer` of cookie-bearing unsafe requests against an allow-list. A
malicious cross-site POST carries the attacker's `Origin` and is rejected with `403` (`code:
"csrf_failed"`); a same-origin request from the SPA carries an allowed `Origin` and passes; a request with
no `Origin` (server-to-server, native clients, tests) is not a browser-CSRF vector and is allowed. This
needs **no client change**, which is why it is non-breaking. SameSite=lax on the cookie remains a second
layer.

### Refresh-token security review

The existing refresh flow already rotates tokens within a family and detects reuse of a consumed token,
revoking the whole family on detection. S2-T8 adds auditing to that path (`security.refresh_reuse_detected`),
plus the session-management surface above (list/revoke) and the concurrency cap. The token is stored only as
a SHA-256 hash; the cookie is httpOnly, SameSite=lax, and scoped to `/api/v1/auth`.

### API abuse monitoring

`AbuseMonitor` counts rate-limit blocks per IP and flags IPs that cross `abuse_alert_threshold` into a
Redis sorted set (pruned by age). Platform admins read a snapshot at `GET /api/v1/security/abuse`:
currently flagged IPs, count of locked accounts, and the active thresholds. Crossing the threshold also
emits `security.abuse_detected`.

### Security-event auditing

All of the above write through `app/modules/security/audit.py` into the existing `audit_logs`. Security
events are **platform-scope** (`organization_id` NULL): they appear in the platform audit feed and are
hidden from tenant feeds. The background writer opens its own short-lived system session and never raises —
a failed audit write cannot break the request. Non-IP hosts are coerced to NULL before the `inet` cast.
Event actions include `security.login_failed`, `security.login_succeeded`, `security.login_blocked`,
`security.refresh_reuse_detected`, `security.logout`, `security.password_reset`, `security.session_revoked`,
`security.sessions_revoked_others`, `security.session_evicted`, `security.rate_limited`,
`security.csrf_blocked`, and `security.abuse_detected`.

## Configuration

All settings live in `app/core/config.py` with safe defaults: header toggles and values; rate-limit
enable/window/global/auth limits; lockout failures/window/duration and per-IP failure ceiling; abuse alert
threshold; password length/classes/common-block; max concurrent sessions; and CSRF enable plus an optional
explicit origin allow-list (falling back to the CORS origins and the frontend URL).

## Middleware order

`CORS → SecurityHeaders → RateLimit → CSRF → AccessLog → RequestID → Tenancy`. CORS stays outermost so
preflight and CORS headers are unaffected; security headers wrap all responses; rate limiting runs before
the heavier request work; CSRF runs before routing.

## Validation

Validated live against PostgreSQL 16 + Redis 7 via the FastAPI test client. A dedicated security e2e
(34 checks) covers headers, password policy, lockout (including the no-enumeration generic `401`), session
list/revoke/delete, refresh-reuse detection, CSRF origin verification, the platform security-audit feed
(with tenant-feed isolation), and the abuse dashboard. A separate rate-limit e2e (5 checks) confirms the
`429` envelope, `Retry-After`, and that non-auth traffic is unaffected. The full regression — auth (18),
tenancy (11), organizations (19), RBAC (20), audit (21), and the pytest unit/integration RLS suite (36) —
remains green with all controls active, demonstrating no breaking changes.
