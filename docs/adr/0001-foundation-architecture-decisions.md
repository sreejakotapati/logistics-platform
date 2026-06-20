# ADR-0001: Foundation Architecture Decisions

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Engineering Manager, Solution Architect (approved by project owner)

## Context
The Logistics Management Platform is a fresh, multi-tenant SaaS build that must scale to thousands
of organizations and millions of shipment records, with strong tenant isolation, India-first
compliance, and a path to extensibility. The foundational decisions below were reviewed and locked
before implementation; they propagate through all sprints and are costly to reverse later.

## Decision
The following are **Accepted** and may not be reopened without a superseding ADR and EM approval.

1. **Multi-tenancy:** shared schema + `organization_id` on every business table + **PostgreSQL
   Row-Level Security**, enabled from the first migration.
2. **Identity & membership:** global `users`; **multi-organization membership** via
   `user_organizations`; roles are organization-scoped.
3. **Organization switching:** **JWT-based active-organization context** — the active
   `organization_id` is a signed token claim that sets the RLS context per request; switching
   organizations issues a **new JWT**. Org context is never taken from a client header.
4. **Organization onboarding:** support **both** self-service registration and Super Admin
   provisioning.
5. **Team membership:** many-to-many via `team_members`; a user may belong to multiple teams; exactly
   one team may be marked **primary** per user per org.
6. **Deployment topology:** **modular monolith** (single FastAPI app, clean module boundaries),
   not microservices.
7. **Primary keys:** **UUIDv7**; standard audit columns, soft delete, optimistic locking on every
   business table.
8. **Auth tokens:** short-lived JWT access token + rotating refresh token (httpOnly cookie).
9. **Notification providers:** abstraction interfaces `EmailProvider`, `SmsProvider`,
   `WhatsAppProvider`, `PushProvider`; initial adapters **AWS SES, MSG91, Meta WhatsApp Business
   API, Firebase Cloud Messaging**. Provider choice is configuration, not code change.
10. **Scope:** **India-first** — GSTIN, E-Way Bill, Indian PIN codes, INR — with the architecture
    kept extensible for future countries (country field + pluggable tax/address/currency rules).

## Consequences
- Tenant isolation is enforced at the database layer (defense-in-depth) — a missing app-layer filter
  cannot leak data, but every table and migration must carry `organization_id` and RLS policies.
- The auth/session model is more involved (active-org claim, org-switch reissues tokens), but RLS
  context is tamper-resistant.
- The modular monolith keeps operations simple now while preserving the option to extract services
  later; microservices are explicitly deferred.
- India-first features ship without blocking future-country extension.

## Alternatives considered
- Database-per-tenant / schema-per-tenant: rejected for operational unmanageability at thousands of
  tenants.
- Single-organization identity: rejected in review in favour of multi-org membership.
- Header-based org context: rejected as tamper-prone versus a signed JWT claim.
- Microservices from day one: rejected as premature operational overhead.
