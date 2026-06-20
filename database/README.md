# Database

PostgreSQL 16 · shared-schema multi-tenancy (`organization_id` + RLS) · UUIDv7 keys.

## Folder structure
```
database/
  init/                      # container bootstrap (once, as superuser)
    01_extensions.sql        # pgcrypto
    02_roles.sh              # app_user (runtime), logistics_migrator (DDL), app_superadmin (BYPASSRLS)
  migrations/                # reserved for raw SQL artifacts/exports if ever needed
  seeds/                     # seed data (permission catalog, system roles) — Sprint 2
  README.md
```
Versioned schema (the `app` schema, functions, RLS helpers, grants, and later all tables) is managed
by **Alembic** in `backend/alembic/` — not here.

## Initialization strategy
1. **Bootstrap** (first container start, owner/superuser): `database/init/` is mounted to
   `/docker-entrypoint-initdb.d` → installs extensions and creates roles. No tables.
2. **Foundation** (Alembic `0001_foundation`, migration role): `app` schema + UUIDv7 +
   `current_org_id` + `set_updated_at` + `enable_org_rls` + grants/default privileges.
3. **Modules** (Sprint 2 onward): entity tables, each calling `app.enable_org_rls` per the
   migration checklist.

See `docs/architecture/database-architecture.md`, `docs/architecture/multi-tenancy.md`,
`docs/architecture/database-naming-conventions.md`, and `docs/guides/migrations.md`.

## What is intentionally NOT here (S1-T3 scope)
No business or entity tables — not Orders/Shipments/Customers/Vendors/Drivers/Vehicles/Warehouses,
and not yet Organizations/Users/RBAC/Audit (those are Sprint 2). S1-T3 builds only the foundation.
