# Coding Standards

Conventions that keep the codebase consistent and reviewable. Tooling enforces most of these in CI.

## Universal
- Small, focused changes; clear names; comments explain **why**, not what.
- Respect the locked decisions ([ADR-0001](docs/adr/0001-foundation-architecture-decisions.md)).
- Every tenant-scoped table carries `organization_id` and enables **RLS** — never filter tenancy in
  application code alone. See [multi-tenancy](docs/architecture/multi-tenancy.md).

## Backend (Python · FastAPI · SQLAlchemy 2 async)
- **Layering:** `router → service → repository → model`. Routers do no DB work; services own the
  unit-of-work (commit/rollback); repositories own queries. See
  [backend-architecture](docs/architecture/backend-architecture.md).
- **Async** throughout (async engine/sessions). Use the shared `BaseRepository` / `BaseService`.
- **Schemas:** Pydantic v2; response models read from ORM (`from_attributes`).
- **Errors:** raise the `AppError` hierarchy; handlers emit the standard error envelope. Don't leak
  stack traces.
- **Tables:** inherit the foundation mixins (UUIDv7 PK, timestamps, audit, soft delete, version).
  Naming: [database-naming-conventions](docs/architecture/database-naming-conventions.md).
- **Style:** `ruff` (lint/format) and `mypy` (types) must pass. Tests with `pytest`.

## Frontend (TypeScript · Next.js 15 · Tailwind · ShadCN)
- **App Router**; the authenticated surface lives under the `(app)` route group inside `AppShell`.
- **State:** React Query for server state; Zustand for ephemeral UI state. No business state in S1.
- **Design tokens** only (CSS variables + Tailwind utilities); use the status spine tokens for
  logistics statuses. See [frontend-architecture](docs/architecture/frontend-architecture.md).
- **Imports:** use the `@/` alias. Components are typed; no `any` without justification.
- **Style:** `next lint` + `tsc --noEmit` must pass; Prettier for formatting.

## SQL & migrations
- One migration per logical change; reversible where practical. Migrations run as the **migrator**
  role. Guide: [migrations](docs/guides/migrations.md).

## Commits & branches
Conventional Commits; trunk-based branches; squash-merge. See [Git Workflow](docs/guides/git-workflow.md).
