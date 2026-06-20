# Backend (FastAPI)

Modular-monolith FastAPI service. Foundation scaffolded in **S1-T5** (no business modules yet).

## Layout
```
app/
  main.py            # app factory, lifespan/bootstrap, middleware + router wiring
  core/              # config · logging · exceptions · security primitives · redis
  db/                # base (Declarative Base + mixins) · session (engine, tenancy, health)
  shared/            # base_repository · base_service · schemas · pagination · responses · deps (DI)
  middleware/        # request_id · access logging
  api/               # health (/health, /ready) · v1/router (empty aggregator)
  modules/           # business modules — added Sprint 2 (router→service→repository)
alembic/             # migrations (baseline 0001_foundation from S1-T3)
tests/               # unit / integration / api
```

## Run
```bash
# from repo root, with the stack up:
make up                 # backend builds & runs once deps are installed in the image
# or locally:
cd backend
pip install -r requirements-dev.txt
export DATABASE_URL=... REDIS_URL=... JWT_SECRET=...
uvicorn app.main:app --reload
```
- `/health` (liveness) · `/ready` (DB+Redis) · `/docs` (OpenAPI) · `/api/v1` (empty until S2)

## Tests
```bash
pytest            # includes the /health smoke test
```

## Not implemented here (by design)
No Auth, Users, Organizations, RBAC, Audit, or any business entities — only the foundation.


---
**See also:** [Backend architecture](../docs/architecture/backend-architecture.md) · [Multi-tenancy & RLS](../docs/architecture/multi-tenancy.md) · [Migrations](../docs/guides/migrations.md) · [Coding Standards](../CONVENTIONS.md) · [Docs index](../docs/README.md)
