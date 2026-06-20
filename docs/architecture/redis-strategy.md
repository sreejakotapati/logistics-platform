# Redis Strategies

Foundational strategy for each workload. Implementations land in later sprints — this defines the
patterns, key shapes, and TTLs so they stay consistent.

## 1. Cache strategy
- **What to cache:** resolved RBAC permission sets per (user, active org), feature-flag evaluations
  per org, and hot, slow-changing reference data. Never cache tenant data without the org in the key.
- **Pattern:** read-through with a TTL; on write, invalidate (delete) the key and optionally publish
  on an invalidation channel so other instances drop their local copies.
- **TTL:** short for permission/flag caches (e.g. minutes) with explicit invalidation on change;
  versioned where needed (`permissions_version`) to force refresh.
- **Stampede protection:** a short-lived lock key (`lock:...`) guards expensive recomputation.
- **Keys:** `cache:org:<org_id>:<entity>:<id>` (see key conventions).

## 2. Session strategy
- **Access tokens are stateless JWTs** (carry the active org claim) — not stored in Redis.
- **Redis holds the fast path for refresh/session control:** a refresh-token/session record keyed by
  its `jti`, and a **denylist** for immediate revocation (logout, rotation reuse, org switch).
- **Source of truth** for refresh tokens remains the database (`refresh_tokens`, S2); Redis is the
  low-latency lookup/denylist layer.
- **TTL** matches the refresh-token lifetime; denylist entries expire when the token would have.
- **Keys:** `session:refresh:<jti>`, `session:denylist:<jti>`, `session:user:<user_id>:*`.

## 3. Pub/Sub strategy
- **Purpose:** fan-out across backend instances — primarily **WebSocket** delivery (live tracking,
  notifications) so a message published by one instance reaches subscribers on any instance.
- **Channels:** `ws:org:<org_id>:<topic>` for tenant-scoped realtime; `events:<domain>` for internal
  domain events; `cache:invalidate` and `flags:invalidate` for cache busting.
- **Semantics:** Pub/Sub is fire-and-forget (no persistence, no replay). **Durable, at-least-once
  delivery uses Streams** (see queues, below) — not Pub/Sub.
- Buffer tuning for many subscribers is set in `redis.conf` (`client-output-buffer-limit pubsub`).

## 4. Rate limiting strategy
- **Scopes:** per IP (pre-auth), per user, and per organization (tenant quotas).
- **Algorithm:** sliding-window or token-bucket using atomic `INCR` + `EXPIRE` (fixed window) or a
  sorted set of timestamps (sliding window); centralized in Redis so limits hold across instances.
- **Response:** standard `429` with `Retry-After`; limits are configurable per route/tier.
- **Keys:** `ratelimit:<scope>:<id>:<window>` (e.g. `ratelimit:ip:1.2.3.4:1m`).

## Future workloads (reserved — NOT implemented in S1-T4)
- **Notification queues:** Redis **Streams** with consumer groups for at-least-once processing across
  email/SMS/WhatsApp/push. Keys: `stream:notifications:<channel>`. (S3 / S7)
- **Background jobs:** a Redis-backed queue (candidate libraries: `arq` or Celery+Redis — decision via
  ADR) plus distributed locks. Keys: `queue:<name>`, `job:<id>`, `lock:<resource>`. (S6+)
- **Feature flags:** per-org evaluation cache `flag:org:<org_id>:<key>` invalidated via the
  `flags:invalidate` channel. (S3)
