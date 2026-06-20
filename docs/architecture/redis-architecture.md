# Redis Architecture

## Role in the platform
Redis 7 is the platform's in-memory backbone for **six workloads**, all of which this task lays the
foundation for (none are implemented yet):

| Workload | Data structure | Sprint it lands |
|---|---|---|
| Session caching | strings/hashes + TTL | S2 (auth) |
| Rate limiting | INCR + EXPIRE / sorted sets | S2+ |
| Feature-flag cache | strings/hashes + TTL + invalidation channel | S3 |
| Notification queues | **Streams** + consumer groups | S3 / S7 |
| WebSocket fan-out | **Pub/Sub** | S7 |
| Background jobs | queue (Streams) + distributed locks | S6+ |

## Topology & scaling
- **Dev:** a single Redis instance (this compose service).
- **Production roadmap:** Redis Sentinel or Cluster for HA. Durable workloads (queues/jobs/streams)
  may move to a **dedicated instance** separate from the volatile cache instance, so the cache can run
  `allkeys-lru` while the durable store runs `noeviction`. Designed for, not built now.

## Logical database & namespacing
- The platform uses **DB 0 only**; workloads are separated by **key namespaces** (see the key
  conventions doc). This keeps the design compatible with Redis Cluster (which supports a single DB).

## Multi-tenancy
Org-scoped Redis data carries the organization in the key (`...:org:<organization_id>:...`). The
active organization comes from the request's JWT context — consistent with the database RLS model.

## Persistence & eviction
- **AOF `everysec` + RDB** for durability of streams/queues/jobs.
- **`noeviction` + per-key TTLs** for now; cache keys always set a TTL so they self-expire. At scale,
  split volatile cache (`allkeys-lru`) from the durable store.

## Client strategy (wired in S1-T5, not here)
- One async `redis-py` connection pool, configured from `REDIS_URL`.
- Planned backend layout (created later): `app/core/redis.py` (pool/health), and helpers under
  `app/shared/` for cache, session, pub/sub, and rate limiting. No code in S1-T4.

## Health
The container exposes a `redis-cli ping` health check (see compose). The backend adds a Redis check to
`/ready` in S1-T5.
