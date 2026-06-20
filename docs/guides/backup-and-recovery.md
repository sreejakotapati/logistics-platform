# Backup & Recovery (Foundation)

## What is backed up
- **PostgreSQL** (system of record) — logical dumps via `pg_dump`. This is the primary backup.
- **Redis** — treated as cache/ephemeral; AOF/RDB persistence on its volume covers restart recovery.
  It is not part of the logical backup set.
- **Volumes** — `pgdata` (and uploaded files later) should also be covered by host/volume snapshots
  where available.

## Taking backups
```bash
make staging-backup
# or: BACKUP_DIR=./backups RETENTION_DAYS=7 bash scripts/backup-postgres.sh
```
Produces `backups/logistics-<timestamp>.sql.gz` and prunes dumps older than the retention window.
`backups/` is git-ignored.

## Scheduling
Run the script from host cron (foundation-friendly; no extra services):
```
# daily at 02:30
30 2 * * *  cd /opt/logistics-platform && BACKUP_DIR=/var/backups/logistics bash scripts/backup-postgres.sh >> /var/log/logi-backup.log 2>&1
```
Ship the resulting files **offsite** (object storage / another host) — keeping them only on the same
host is not a real backup.

## Restore
```bash
# stop the app so nothing writes mid-restore
docker compose -f docker-compose.staging.yml --env-file .env.staging stop backend frontend

# restore into the running Postgres container
gunzip -c backups/logistics-<timestamp>.sql.gz | \
  docker compose -f docker-compose.staging.yml --env-file .env.staging exec -T postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

docker compose -f docker-compose.staging.yml --env-file .env.staging start backend frontend
```

## Targets (foundation)
- **RPO:** ≤ 24h with daily dumps (tighten with more frequent dumps / WAL archiving later).
- **RTO:** minutes — restore a dump and restart. Test restores periodically; an untested backup is a
  hope, not a backup.
