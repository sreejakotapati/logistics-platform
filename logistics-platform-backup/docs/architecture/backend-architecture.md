# Backend Architecture (Foundation)

## Clean architecture layers
```
API (routers)  ->  Service (business rules, unit-of-work)  ->  Repository (queries)  ->  Models/DB
            shared DI · schemas · pagination · responses
   cross-cutting: config · logging · exceptions · security · middleware · redis
```
Routers never touch the DB directly; services own transactions; repositories own queries. Business
modules (Sprint 2+) follow `app/modules/<name>/{router,service,repository,schemas,models}.py`.

## Dependency graph
```mermaid
flowchart TD
    main[main.py / create_app] --> mw[middleware: request_id, access_log, CORS]
    main --> ex[exception handlers]
    main --> health[/health, /ready/]
    main --> v1[/api/v1 router (empty)/]
    health --> dbh[db.session.check_database]
    health --> rdh[core.redis.check_redis]
    subgraph DI [shared/deps]
      getdb[get_db -> AsyncSession]
      getredis[get_redis -> Redis]
      page[PaginationParams]
    end
    getdb --> sess[db.session: engine + sessionmaker]
    getredis --> rds[core.redis: client]
    svc[BaseService] --> repo[BaseRepository] --> sess
    cfg[core.config.Settings] --> sess
    cfg --> rds
```

## Startup / bootstrap flow
1. `create_app()` configures JSON logging, builds the `FastAPI` app, installs middleware
   (CORS → access-log → request-id), registers exception handlers, and mounts routers.
2. On startup, the **lifespan** initializes the DB engine + session factory and the Redis client
   (objects only; the first real connection is lazy).
3. Requests flow: request-id assigned → access logged → routed → (service → repository → session) →
   standard JSON response; errors become the standard error envelope.
4. On shutdown, the engine is disposed and the Redis client closed.

## Tenancy hook (wired in Sprint 2)
`db.session.set_current_org_id(session, org_id)` issues `SET LOCAL app.current_org_id = ...` from the
JWT's active-org claim so RLS scopes every query. No auth/tenancy enforcement exists yet.

## Health vs readiness
- `/health` — liveness; returns 200 without touching dependencies.
- `/ready` — readiness; returns 200 only if DB and Redis are reachable, else 503 with per-check status.
