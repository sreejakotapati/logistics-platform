#!/usr/bin/env bash
# Deploy the staging stack with Docker Compose (cloud-agnostic). Idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env.staging}"
COMPOSE="docker compose -f docker-compose.staging.yml --env-file ${ENV_FILE}"

[ -f "$ENV_FILE" ] || { echo "Missing ${ENV_FILE} (copy from .env.staging.example)"; exit 1; }

echo "==> Building images"
$COMPOSE build

echo "==> Starting data tier (postgres, redis)"
$COMPOSE up -d postgres redis

echo "==> Waiting for Postgres to be healthy"
until $COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-logistics_owner}" >/dev/null 2>&1; do
  sleep 2
done

echo "==> Applying database migrations"
$COMPOSE run --rm backend alembic upgrade head

echo "==> Starting application + reverse proxy"
$COMPOSE up -d

echo "==> Waiting for backend readiness (db + redis)"
for i in $(seq 1 30); do
  if $COMPOSE exec -T backend curl -fsS http://localhost:8000/ready >/dev/null 2>&1; then
    echo "==> Staging is up and ready."
    exit 0
  fi
  sleep 5
done

echo "Backend did not become ready in time. Check: $COMPOSE logs backend" >&2
exit 1
