# Architecture Navigation Guide

Where to find each part of the design, and the decisions that bind them.

## Locked decisions (ADR-0001)
All recorded in **[ADR-0001](../adr/0001-foundation-architecture-decisions.md)**; don't reopen without
a new ADR ([ADR Guide](../adr/README.md)).

1. **Multi-tenancy** — shared schema + `organization_id`. → [multi-tenancy](multi-tenancy.md)
2. **PostgreSQL RLS** — enforced on every tenant table; runtime role can't bypass. → [multi-tenancy](multi-tenancy.md) · [database](database-architecture.md)
3. **JWT active-organization context** — active org is a signed claim that sets the RLS GUC per request; switching mints a new token. → [backend](backend-architecture.md)
4. **Onboarding** — self-service registration **and** Super Admin provisioning.
5. **Team membership** — many-to-many; multi-team; one primary per user per org.
6. **Modular monolith** — one deployable, clear module boundaries. → [backend](backend-architecture.md)
7. **Data conventions** — UUIDv7 PKs, audit columns, soft delete, optimistic locking. → [naming](database-naming-conventions.md)
8. **Auth tokens** — short-lived access JWT + rotating refresh (httpOnly cookie).
9. **Notification provider abstraction** — Email/SMS/WhatsApp/Push interfaces; adapter = config.
10. **India-first** — GSTIN, e-way bill, PIN codes, INR; extensible to other countries.

## Documents by area
- **Backend:** [backend-architecture](backend-architecture.md) — layers, DI, startup, request lifecycle, tenancy hook.
- **Frontend:** [frontend-architecture](frontend-architecture.md) — providers, layout system, tokens, state split.
- **Database:** [database-architecture](database-architecture.md) · [multi-tenancy](multi-tenancy.md) · [naming](database-naming-conventions.md)
- **Redis:** [redis-architecture](redis-architecture.md) · [strategy](redis-strategy.md) · [key conventions](redis-key-conventions.md)
- **Infrastructure:** [infrastructure](infrastructure.md) — staging foundation, networks, volumes, overlays.

## How a feature is built (Sprint 2+)
A module lives in `backend/app/modules/<name>/` as `router → service → repository → models`, with
`organization_id` + RLS on its tables, a feature flag where rollout matters, and any notifications
sent through the provider abstraction. The frontend surfaces it under the `(app)` route group.
