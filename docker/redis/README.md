# Redis container

Official `redis:7-alpine` with `redis.conf` mounted read-only; started via
`redis-server /usr/local/etc/redis/redis.conf` (see `docker-compose.yml`).

- **Single logical database (DB 0).** All workloads share DB 0 and are separated by **key
  namespaces** (cluster-friendly; multiple DBs are avoided).
- **Persistence:** AOF (`everysec`) + RDB snapshots; the `redisdata` volume survives restarts
  (`make reset` wipes it).
- **No auth locally;** production sets `requirepass` and `REDIS_URL` includes credentials.

See: `docs/architecture/redis-architecture.md`, `docs/architecture/redis-strategy.md`,
`docs/architecture/redis-key-conventions.md`, `docs/guides/redis-local-development.md`.

## Folder layout
```
docker/redis/
  redis.conf     # the configuration above
  README.md
```
The backend Redis code (client pool, cache/session/pubsub/ratelimit helpers) is scaffolded in S1-T5
under `backend/app/core/redis.py` and `backend/app/shared/` — not created in S1-T4.
