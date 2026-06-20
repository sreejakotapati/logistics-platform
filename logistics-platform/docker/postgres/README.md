# PostgreSQL container config

- **Tuning:** `postgresql.conf` here is the reference tuning. It is applied via `-c` flags in the
  `postgres` service `command` in `docker-compose.yml` (layered on top of image defaults — a safe,
  non-replacing approach).
- **Bootstrap SQL** (extensions + roles) lives in `database/init/` and is mounted into the container's
  `/docker-entrypoint-initdb.d` (runs once on first start, as the owner/superuser).
- **Versioned schema** (the `app` schema, functions, RLS helpers, grants — and later all tables) is
  managed by **Alembic** in `backend/alembic/`. No tables are created in S1-T3.
