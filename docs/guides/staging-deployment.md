# Staging Deployment Guide

Cloud-agnostic deployment with Docker Compose. Prerequisites: Docker + Compose v2 on the host, DNS
for `STAGING_DOMAIN` pointing at it (or use `staging.localhost` with `tls internal`).

## 1. Configure
```bash
cp .env.staging.example .env.staging
chmod 600 .env.staging
# edit .env.staging: set STAGING_DOMAIN, ACME_EMAIL, all __set_strong_secret__ values,
# and keep DATABASE_URL/MIGRATION_DATABASE_URL passwords in sync with the role passwords.
```

## 2. Deploy
```bash
make staging-deploy        # build -> start db/redis -> migrate -> start app+proxy -> health wait
# or: bash scripts/deploy-staging.sh
```
The script applies the Alembic foundation migration via a one-off `backend` container before starting
the app, then polls `/ready` (DB + Redis) before reporting success.

## 3. Verify
```bash
make staging-logs
curl -fsS https://$STAGING_DOMAIN/health      # liveness (through Caddy)
curl -fsS https://$STAGING_DOMAIN/api/v1/...  # API base (modules from Sprint 2)
```

## 4. Update / redeploy
Re-run `make staging-deploy` — it rebuilds, re-applies migrations (no-op if none), and restarts.

## 5. Rollback (foundation)
- Code: deploy a previous git tag/image and re-run the deploy.
- Data: restore from a backup (see `backup-and-recovery.md`). Migrations are forward-only; a
  destructive change needs a tested down-path or a restore.

## 6. Teardown
```bash
make staging-down                 # stop (keep volumes/data)
docker compose -f docker-compose.staging.yml --env-file .env.staging down -v   # also delete data
```

## Optional: monitoring & logging
```bash
make monitoring-up    # Prometheus :9090, Grafana :3001 (localhost-bound)
make logging-up       # Loki :3100 + Promtail
```
