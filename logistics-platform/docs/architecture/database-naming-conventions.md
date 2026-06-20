# Database Naming Conventions

These are enforced in code by the Alembic `naming_convention` in `backend/alembic/env.py`.

## Tables & columns
- Tables: `snake_case`, plural (`user_organizations`, `notification_logs`).
- Columns: `snake_case`.
- Primary key: `id uuid` defaulting to `app.uuid_generate_v7()`.
- Tenant key: `organization_id uuid` on every business table.
- Audit columns: `created_at, updated_at, created_by, updated_by, deleted_at, version`.
- Booleans: `is_*` / `has_*`. Timestamps: `*_at`. Foreign keys: `<referenced_singular>_id`.

## Constraints & indexes (auto-named)
| Kind | Pattern |
|---|---|
| Primary key | `pk_<table>` |
| Index | `ix_<table>_<cols>` |
| Unique | `uq_<table>_<cols>` |
| Check | `ck_<table>_<name>` |
| Foreign key | `fk_<table>_<col>_<referred_table>` |

## Other objects
- Schema for shared helpers: `app`.
- Functions: `snake_case` in `app` (`app.uuid_generate_v7`, `app.enable_org_rls`).
- RLS policy name (standard): `org_isolation`.
- Enums: `snake_case` type name and values.
- Migration revisions: `NNNN_slug` (e.g. `0001_foundation`, `0002_organizations`).
