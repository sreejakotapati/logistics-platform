# PostgreSQL Architecture

## Engine & model
- **PostgreSQL 16**, single shared database, **shared-schema multi-tenancy**: every business row
  carries `organization_id`; isolation is enforced by **Row-Level Security**.
- **UUIDv7** primary keys via `app.uuid_generate_v7()` (time-ordered → good index locality).

## Role architecture (why four roles)
| Role | Privileges | Used by | RLS |
|---|---|---|---|
| owner (`POSTGRES_USER`) | superuser/owner | container bootstrap only | bypasses (bootstrap only) |
| `app_user` | NOSUPERUSER, **NOBYPASSRLS** | the backend at runtime | **enforced** |
| `logistics_migrator` | DDL, owns objects | Alembic migrations | enforced (DDL unaffected) |
| `app_superadmin` | **BYPASSRLS** | platform cross-tenant ops only | bypasses by design |

> Critical: the runtime role must NOT be a superuser and must NOT have `BYPASSRLS`, or RLS is
> silently ignored. `FORCE ROW LEVEL SECURITY` additionally subjects the table owner to the policy.

## Connection strategy
- Backend → `DATABASE_URL` (as `app_user`). RLS applies to every query.
- Alembic → `MIGRATION_DATABASE_URL` (as `logistics_migrator`).
- Platform/super-admin cross-tenant work → a separate connection as `app_superadmin` (BYPASSRLS),
  used sparingly and audited.

## Foundation objects (created in S1-T3, schema `app`)
- `app.uuid_generate_v7()` — UUIDv7 generator.
- `app.current_org_id()` — reads the per-request active org GUC.
- `app.set_updated_at()` — trigger function for `updated_at`.
- `app.enable_org_rls(regclass)` — applies the standard isolation policy to a table.

## What is NOT here yet
No business or entity tables. `organizations`, `users`, `user_organizations`, RBAC, audit, etc. are
Sprint-2 module migrations that build on this foundation.

## Bootstrap vs versioned
- **Bootstrap** (once, superuser): extensions + roles via `database/init/`.
- **Versioned** (Alembic): the `app` schema, functions, RLS helpers, grants — and later all tables.
