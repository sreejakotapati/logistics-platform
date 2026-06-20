# Logistics Management Platform — Agent Team Charter

This file orchestrates a multi-agent engineering team building the multi-tenant Logistics
Management Platform. It defines how the ten specialist agents under `.claude/agents/` collaborate,
the locked decisions they must honour, the approved roadmap, and the pipeline they move work through.

> **Authoritative source documents** (never contradict these; raise conflicts, do not silently diverge):
> 1. `CLAUDE.md` (master charter) — product scope, stack, coding/security standards.
> 2. **Architecture v2** — shared-schema + Postgres RLS, multi-org membership, modular monolith, RBAC, flags, audit.
> 3. **Database Design** — 17 foundation tables, RLS policies, UUIDv7, standard audit columns.
> 4. **API Design** — `/api/v1` REST surface, auth + org-switch flow.
> 5. **UI/UX Architecture** — four surfaces, design system, the 8-status logistics spine.
> 6. **Execution Plan + Tracker** — phases, milestones, RACI, risks, DoD.

## Approved roadmap (11-sprint development order — FINAL)

| Sprint | Theme | Modules |
|---|---|---|
| S1 | Foundations | Docker · Env setup · PostgreSQL · Redis · Backend scaffold · Frontend scaffold |
| S2 | Secure core | Authentication · Users · Organizations · RBAC · Audit Logs |
| S3 | Org structure & platform services | Departments · Teams · Notifications · Feature Flags |
| S4 | Master data | Customers · Vendors · Warehouses |
| S5 | Booking spine | Orders · Shipments · AWB |
| S6 | Fleet | Drivers · Vehicles · Trips · Assignment · Dispatch · Maintenance |
| S7 | Realtime tracking | WebSocket gateway · GPS ingestion · Live map · Customer track · Notification triggers |
| S8 | Billing & compliance | Rate cards · Invoices · Payments · GST · E-Way Bill |
| S9 | Analytics | Aggregation layer · Role dashboards · Report builder · Exports |
| S10 | AI services | ETA · Route optimization · Demand forecasting · Anomaly detection |
| S11 | Hardening & release | Security · Pen-test · Load/perf · Regression · UAT · Observability · DR · Go-live |

~11 two-week sprints (~5.5 months). Heaviest sprints (S2, S8, S10) may split under a small team;
buffer is held after S8 and S10 scope is kept flexible.

## Locked architecture decisions (FINAL — do not reopen without an ADR + EM approval)

1. **Organization switching — JWT-based active-org context.** The active `organization_id` is embedded
   as a claim in the access token and sets the RLS context per request. Switching organizations issues a
   **new JWT** scoped to the chosen org. Org context is never taken from a client-supplied header.
2. **Organization onboarding — both paths.** Support (a) self-service organization registration and
   (b) Super Admin organization provisioning. Both create an org + an initial Org Admin membership.
3. **Team membership — many-to-many via `team_members`.** A user may belong to multiple teams; exactly
   one team may be marked **primary** per user per org (enforced by constraint).
4. **Notification providers — provider abstraction interfaces** `EmailProvider`, `SmsProvider`,
   `WhatsAppProvider`, `PushProvider`. Initial concrete adapters: **Email = AWS SES · SMS = MSG91 ·
   WhatsApp = Meta WhatsApp Business API · Push = Firebase Cloud Messaging (FCM)**. Adapters are swappable
   behind the interfaces; provider choice is configuration, not code change.
5. **India-first scope lock** — **GSTIN, E-Way Bill, Indian PIN codes, INR currency**. The architecture
   stays extensible for future countries (country field + pluggable tax/address/currency rules); no
   non-India logic ships in this release, but nothing hard-codes India in a way that blocks extension.

## Shared non-negotiables (every agent honours these)

- **Tenant isolation is sacred.** Every business record carries `organization_id`; RLS is enabled from the
  first migration. No code path may read or write across organizations. A missing tenant filter is a
  release-blocking defect.
- **Identity is global, membership is the tenant boundary.** Users are global; `user_organizations` scopes
  them. The active organization lives in the JWT (decision #1) and sets the RLS context per request.
- **RBAC is database-driven.** Permission checks only — never hard-coded role-name checks in business logic.
- **Feature flags gate capability.** Gated modules never render or execute unless enabled for the active org.
- **Master-charter standards always apply:** UUIDv7 PKs, audit columns, soft delete, repository + service
  patterns, validation, error handling, security, ≥80% coverage. Never generate demo/toy code; never skip
  validation, testing, error handling, or security.
- **Status vocabulary is fixed:** `Not started` · `In progress` · `Blocked` · `Done`.

## The agent team

| Agent | Owns | Primary sprint(s) |
|---|---|---|
| `product-manager` | Scope, priorities, acceptance criteria, roadmap | All |
| `business-analyst` | Detailed specs, process flows, traceability | All |
| `solution-architect` | System architecture, ADRs, NFRs, module boundaries | S1–S2, advisory after |
| `database-architect` | Schema, RLS, migrations, indexing, performance | S2–S3, advisory after |
| `ui-ux-designer` | Design system, surfaces, flows, accessibility | S1, continuous |
| `backend-engineer` | FastAPI modules, APIs, auth, RBAC, business logic | S2–S10 |
| `frontend-engineer` | Next.js surfaces, components, state | S1–S10 |
| `ai-engineer` | ETA, route optimization, forecasting, anomaly detection | S10 |
| `qa-engineer` | Test strategy, isolation suite, coverage, regression, UAT | All |
| `devops-engineer` | Docker, CI/CD, environments, observability, release | S1, S7, S11 |

## Work pipeline (handoff chain)

```
product-manager → business-analyst
   → solution-architect · database-architect · ui-ux-designer   (design)
      → backend-engineer · frontend-engineer · ai-engineer       (build)
         → qa-engineer                                           (verify)
            → devops-engineer                                    (release)
```

Each step produces a written handoff artifact referencing the relevant sprint and tracker task IDs. The
**Engineering Manager** is the accountable owner and the escalation point for cross-agent conflicts.

## Definition of Done (team-wide)

- **Task:** reviewed + merged; CI green (lint, type, test, build); org-scoped + RBAC-gated; audit events
  emitted; OpenAPI + UI states updated; coverage ≥80%.
- **Sprint:** all sprint modules delivered; end-to-end journey demoed on staging; isolation suite green; no
  open critical/high defects.
- **Release:** SLAs met under load; pen-test passed (no open criticals); observability + rollback rehearsed;
  UAT signed by pilot org.

## Standard output format (for any deliverable that warrants it)

Requirements → Assumptions → Architecture → Database Design → API Design → Folder Structure →
Implementation Steps → Code → Tests → Deployment Notes → Recommendations.

## Golden rule

Never jump straight to code. Requirements → Architecture → Database → APIs → Implementation → Testing →
Deployment, with the right agent accountable at each step.
