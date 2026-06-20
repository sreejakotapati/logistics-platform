# Troubleshooting

Common issues and fixes. If something here is wrong or missing, fix it in a `docs/` PR.

## Environment & startup
- **`make env-check` fails / app can't read config** — you skipped `make env`. Copy `.env.example`
  to `.env` and re-check. Variables: [environment-variables.md](environment-variables.md).
- **Port already in use (3000/8000/5432/6379)** — another process holds the port. Stop it, or change
  the published port in `.env` / compose, then `make down && make up`.
- **First `make up` is slow** — it's building/pulling images. Use `make up-infra` + run apps locally
  for a faster loop.

## Database
- **Backend `/ready` returns 503 (database: false)** — Postgres isn't up/healthy yet. `make ps`;
  check `make logs`. On a fresh clone, give it a few seconds after `make up`.
- **`alembic upgrade head` permission errors** — migrations must use the **migrator** role
  (`MIGRATION_DATABASE_URL`), not the app role. See [migrations.md](migrations.md).
- **RLS: queries return nothing / "row violates row-level security"** — the active organization
  context isn't set, or you're using the wrong role. The runtime app role must **not** be superuser
  or `BYPASSRLS`, and the request must set the active-org context (JWT claim → GUC). See
  [multi-tenancy.md](../architecture/multi-tenancy.md).
- **Reset everything** — `make reset` tears down and recreates (this **drops data/volumes**).

## Redis
- **`/ready` shows redis: false** — Redis container down or wrong `REDIS_URL`. `make redis-cli` then
  `PING`. Conventions: [redis-local-development.md](redis-local-development.md).

## Backend
- **App won't import/boot** — check `ruff check .` and `mypy app` first; most boot errors are import
  or type issues. The factory builds the app at import; the DB/Redis connect lazily in the lifespan.

## Frontend
- **`npm run build` fails on `NEXT_PUBLIC_*`** — these are inlined at build time. Set them in
  `.env.local` (dev) or as build args (staging). See [environments.md](environments.md).
- **Type or lint errors block the build** — run `npm run type-check` and `npm run lint` locally; CI
  gates on both.

## CI
- **A required check fails** — reproduce locally with the same command (lint/type/test/build). The
  job names and gate policy are in [ci-cd.md](ci-cd.md).

## Staging
- **Caddy can't get a certificate** — DNS for `STAGING_DOMAIN` must point at the host, or use
  `staging.localhost` with `tls internal`. See [staging-deployment.md](staging-deployment.md).

Still stuck? Open a discussion/issue with `make ps`, `make logs`, and the exact command + error.
