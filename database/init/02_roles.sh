#!/bin/bash
# Bootstrap database roles (run once on container init, as the owner/superuser).
# Creates the runtime, migration, and platform super-admin roles. No tables.
#
# Role architecture:
#   - POSTGRES_USER (owner)      : image-created owner/superuser; bootstrap only.
#   - APP_DB_USER (runtime)      : NOSUPERUSER NOBYPASSRLS -> RLS APPLIES. Backend connects as this.
#   - MIGRATION_DB_USER (DDL)    : runs Alembic migrations; owns schema objects.
#   - SUPERADMIN_DB_USER         : BYPASSRLS; cross-tenant platform operations ONLY.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  DO \$do\$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${APP_DB_USER}') THEN
      CREATE ROLE ${APP_DB_USER} LOGIN PASSWORD '${APP_DB_PASSWORD}'
        NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${MIGRATION_DB_USER}') THEN
      CREATE ROLE ${MIGRATION_DB_USER} LOGIN PASSWORD '${MIGRATION_DB_PASSWORD}'
        NOSUPERUSER NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${SUPERADMIN_DB_USER}') THEN
      CREATE ROLE ${SUPERADMIN_DB_USER} LOGIN PASSWORD '${SUPERADMIN_DB_PASSWORD}'
        NOSUPERUSER BYPASSRLS;
    END IF;
  END \$do\$;

  GRANT CONNECT ON DATABASE ${POSTGRES_DB}
    TO ${APP_DB_USER}, ${MIGRATION_DB_USER}, ${SUPERADMIN_DB_USER};

  -- Migration role may create schema objects.
  GRANT CREATE ON DATABASE ${POSTGRES_DB} TO ${MIGRATION_DB_USER};
  GRANT CREATE, USAGE ON SCHEMA public TO ${MIGRATION_DB_USER};

  -- Runtime + super-admin can use public; object-level grants are set by the baseline migration.
  GRANT USAGE ON SCHEMA public TO ${APP_DB_USER}, ${SUPERADMIN_DB_USER};
EOSQL

echo "Roles ensured: ${APP_DB_USER} (runtime), ${MIGRATION_DB_USER} (migrations), ${SUPERADMIN_DB_USER} (bypassrls)."
