# Migration Strategy (Alembic)

## Principles
- **Forward-only, reviewed, reversible.** Every migration has a working `downgrade`. One logical
  change per migration; revisions named `NNNN_slug`.
- **Run as the migration role** (`MIGRATION_DATABASE_URL` → `logistics_migrator`), never the runtime
  or owner role.
- **Expand → migrate → contract** for changes that touch live data, to keep deploys zero-downtime.

## Autogenerate caveats (handle by hand)
Alembic autogenerate does NOT detect: RLS policies, functions/triggers, partial/expression indexes,
grants/default privileges, or check constraints reliably. Write these explicitly with `op.execute`.
The foundation objects (UUIDv7, RLS helpers, grants) live in `0001_foundation`.

## Per-table checklist (Sprint 2 onward)
Every new org-scoped table migration must:
1. Add standard columns: `id` (default `app.uuid_generate_v7()`), `organization_id`,
   `created_at/updated_at/created_by/updated_by`, `deleted_at`, `version`.
2. Add a foreign key `organization_id -> organizations(id)` and an index on `organization_id`.
3. Attach the updated-at trigger:
   `CREATE TRIGGER set_updated_at BEFORE UPDATE ON <t> FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();`
4. Enable isolation: `SELECT app.enable_org_rls('public.<t>');`
5. Add any further indexes the query patterns require.

Global (non-tenant) tables — e.g. `users`, the permission catalog, feature-flag catalog — do NOT get
`organization_id` or `org_isolation`; document why in the migration.

## Data migrations & seeds
- Schema changes go in Alembic; **seed data** (permission catalog, system roles) lives in
  `database/seeds/` and is applied by a separate, idempotent step (Sprint 2).
- Cross-tenant data backfills run as `app_superadmin` (BYPASSRLS) or with an explicit org context.

## Running
```bash
cd backend
export MIGRATION_DATABASE_URL=postgresql+psycopg://logistics_migrator:...@localhost:5432/logistics
alembic upgrade head
```
CI applies migrations against an ephemeral database and runs the isolation suite (Sprint 2+).
