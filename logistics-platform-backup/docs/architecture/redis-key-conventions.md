# Redis Key Naming Conventions

## Format
`<namespace>:<entity>:<id>[:<sub>...]` — lowercase, colon-separated, no spaces or quotes.
Org-scoped data includes an `org:<organization_id>` segment.

## Namespaces
| Namespace | Purpose | Example | TTL |
|---|---|---|---|
| `cache:` | cached reads | `cache:org:<org_id>:permissions:<user_id>` | short, explicit invalidation |
| `session:` | refresh/session + denylist | `session:refresh:<jti>` · `session:denylist:<jti>` | = refresh TTL |
| `ratelimit:` | rate-limit counters | `ratelimit:user:<user_id>:1m` | = window |
| `flag:` | feature-flag cache | `flag:org:<org_id>:<flag_key>` | short |
| `lock:` | distributed locks | `lock:<resource>` | short (lock lease) |
| `stream:` | durable queues (Streams) | `stream:notifications:email` | persistent |
| `queue:` / `job:` | background jobs | `queue:default` · `job:<job_id>` | per job |

## Pub/Sub channels (not keys)
`ws:org:<org_id>:<topic>` · `events:<domain>` · `cache:invalidate` · `flags:invalidate`.

## Rules
- **Tenant scoping:** any org-scoped value must carry `org:<organization_id>`; never mix tenants under
  one key.
- **TTL everywhere it makes sense:** cache, session, rate-limit, lock, and flag keys always set a TTL.
- **No `KEYS` in code:** use `SCAN` with a namespace `MATCH` pattern.
- **Cluster readiness:** when keys for one operation must co-locate on the same slot (e.g. a rate-limit
  window set), wrap the shared part in a hash tag: `ratelimit:{user:<id>}:1m`.
- **Versioning:** prefix with `v1:` only when a breaking format change requires coexistence.
