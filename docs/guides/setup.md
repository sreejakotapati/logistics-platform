# Setup Guide

Detailed prerequisites and first run. For the condensed path see
[Getting Started](../onboarding/README.md).

## Required
- **Docker Engine 24+** and **Docker Compose v2** (`docker compose version`).
- **Git 2.40+**.

## Optional (fast inner loop without rebuilding images)
- **Python 3.12** (backend) and **Node 20** (frontend).
- A Postgres client (`psql`) is handy but not required (`make psql` opens one in the container).

### OS notes
- **macOS / Windows:** Docker Desktop provides Compose v2. On Windows use WSL2.
- **Linux:** install Docker Engine + the `docker-compose-plugin` package.

## First run
```bash
git clone <repo-url> logistics-platform && cd logistics-platform
make env            # .env.example -> .env
make env-check      # verifies required variables are present
make up             # build + start the full stack
```

## What `make up` starts
| Service | Port | Notes |
|---|---|---|
| frontend (Next.js) | 3000 | app shell |
| backend (FastAPI) | 8000 | `/docs`, `/health`, `/ready`, `/api/v1` |
| postgres | 5432 | four-role setup via `database/init` (dev only publishes the port) |
| redis | 6379 | config in `docker/redis/redis.conf` |

Dev auxiliaries are behind the `dev` profile (`make up-dev`): MailHog (email) and MinIO (S3-compatible).

## Running apps locally (optional)
```bash
make up-infra                 # only postgres + redis
# backend
cd backend && pip install -r requirements-dev.txt
uvicorn app.main:app --reload
# frontend (new shell)
cd frontend && npm install && npm run dev
```

## Configuration
All variables are documented in [environment-variables.md](environment-variables.md). The
`DATABASE_URL` uses the **runtime app role** (RLS-enforced); `MIGRATION_DATABASE_URL` uses the
**migrator role**. Never point the app at a superuser — see [multi-tenancy](../architecture/multi-tenancy.md).

## Next
[Local Development Guide](local-development.md) · [Contributing](../../CONTRIBUTING.md) ·
[Troubleshooting](troubleshooting.md)
