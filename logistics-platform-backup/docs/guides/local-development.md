# Local Development Guide

Day-to-day workflow. First-time setup is in the [Setup Guide](setup.md).

## Make targets (the essentials)
`make help` prints everything. Most-used:

| Target | Does |
|---|---|
| `make up` / `make down` | start / stop the full stack |
| `make up-infra` | only Postgres + Redis (run apps locally for fast reloads) |
| `make up-dev` | full stack + dev auxiliaries (MailHog, MinIO) |
| `make logs` / `make ps` | tail logs / list service health |
| `make psql` / `make redis-cli` | open a DB / Redis console in-container |
| `make sh-backend` / `make sh-frontend` | shell into a container |
| `make reset` | tear down and recreate (drops volumes/data) |

## Backend loop
```bash
make up-infra
cd backend && uvicorn app.main:app --reload        # http://localhost:8000
pytest                                             # tests (includes /health smoke test)
ruff check . && mypy app                           # lint + types (CI gates)
alembic upgrade head                               # apply migrations (see migrations guide)
```
Architecture and module layout: [backend-architecture.md](../architecture/backend-architecture.md).
New modules follow `app/modules/<name>/{router,service,repository,schemas,models}.py` and obey
multi-tenancy/RLS (every tenant table sets `organization_id` and enables RLS).

## Frontend loop
```bash
cd frontend && npm install && npm run dev          # http://localhost:3000
npm run lint && npm run type-check                 # CI gates
```
Design tokens, app shell, and state split (React Query vs Zustand):
[frontend-architecture.md](../architecture/frontend-architecture.md).

## Database & migrations
- Migrations run as the **migrator** role via `MIGRATION_DATABASE_URL`; the app runs as the
  **app** role and is bound by RLS. Guide: [migrations.md](migrations.md).
- Inspect with `make psql`. Naming rules: [database-naming-conventions.md](../architecture/database-naming-conventions.md).

## Redis
Cache/session/pub-sub conventions and namespacing: [redis-local-development.md](redis-local-development.md),
[redis-strategy.md](../architecture/redis-strategy.md).

## Before you push
Match what CI checks (lint, types, tests, build). See [Contributing](../../CONTRIBUTING.md),
[Coding Standards](../../CONVENTIONS.md), and the [Definition of Done](../onboarding/definition-of-done.md).
