#!/usr/bin/env bash
# Logical backup of the staging Postgres database (pg_dump -> gzip), with retention pruning.
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="${ENV_FILE:-.env.staging}"
COMPOSE="docker compose -f docker-compose.staging.yml --env-file ${ENV_FILE}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="${BACKUP_DIR}/logistics-${STAMP}.sql.gz"

echo "==> Dumping database to ${FILE}"
$COMPOSE exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-logistics_owner}" \
  -d "${POSTGRES_DB:-logistics}" \
  --no-owner --clean --if-exists | gzip > "$FILE"

echo "==> Pruning backups older than ${RETENTION_DAYS} days"
find "$BACKUP_DIR" -name 'logistics-*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete || true

echo "==> Done. Current backups:"
ls -lh "$BACKUP_DIR"
