# Alembic migrations

- Config: `../alembic.ini`. The DB URL is read from `MIGRATION_DATABASE_URL` (the migration role) in
  `env.py` — never hard-coded.
- Baseline: `versions/0001_foundation.py` creates the `app` schema, UUIDv7, tenancy/RLS helpers, and
  grants. **No business tables.**

## Commands (run from `backend/`)
```bash
export MIGRATION_DATABASE_URL=postgresql+psycopg://logistics_migrator:...@localhost:5432/logistics
alembic upgrade head        # apply
alembic downgrade -1        # revert one
alembic revision -m "create organizations"   # new migration (S2+)
alembic current / history   # inspect
```

## Per-table checklist (S2 onward)
Every org-scoped table migration must: add standard columns (`id` default `app.uuid_generate_v7()`,
`organization_id`, audit columns, `deleted_at`, `version`); create indexes (incl. `organization_id`);
attach the `updated_at` trigger using `app.set_updated_at()`; and call
`SELECT app.enable_org_rls('public.<table>');`. See `docs/guides/migrations.md`.
