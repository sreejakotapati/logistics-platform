# Redis — Local Development

Redis runs as part of the stack (`make up-infra` or `make up`).

## Connect
```bash
make redis-cli            # opens redis-cli in the container
# or:
docker compose exec redis redis-cli
```

## Inspect safely
```bash
PING                      # health
INFO server               # version / uptime
DBSIZE                    # number of keys
SCAN 0 MATCH 'cache:*' COUNT 100   # iterate keys by namespace (NEVER use KEYS in real code)
TTL <key>                 # remaining lifetime
TYPE <key>                # data structure
```

## Watch activity
```bash
MONITOR                   # live command stream (dev only; high overhead)
SUBSCRIBE ws:org:demo:tracking   # observe a Pub/Sub channel
```

## Reset state
```bash
FLUSHDB                   # wipe DB 0 (DEV ONLY)
# or wipe the whole stack's volumes:
make reset
```

## Notes
- Persistence is on (AOF + RDB); data in the `redisdata` volume survives `make down`, and is wiped by
  `make reset`.
- No password locally. If you set `REDIS_PASSWORD` for a prod-like run, update `REDIS_URL` accordingly
  and add `requirepass` to the config.
- Namespaces and TTLs follow `docs/architecture/redis-key-conventions.md`.
