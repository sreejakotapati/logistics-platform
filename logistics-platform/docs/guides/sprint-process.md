# Sprint Process

How work is sequenced. The platform is built in **11 sprints (~5.5 months)** by a multi-agent team
(see `.claude/agents/`), one task at a time with explicit approval gates.

## Roadmap (locked sequence)
| Sprint | Theme |
|---|---|
| **S1** | Foundations — Docker, Postgres/Redis, backend & frontend scaffolds, CI/CD, staging, docs |
| S2 | Auth, Users, Organizations, RBAC, Audit |
| S3 | Departments, Teams, Notifications, Feature Flags |
| S4 | Customers, Vendors, Warehouses |
| S5 | Orders, Shipments, AWB |
| S6 | Fleet |
| S7 | Realtime tracking / WebSockets |
| S8 | Billing, GST, e-way bill |
| S9 | Analytics (+ app `/metrics`) |
| S10 | AI services |
| S11 | Hardening & release |

Heaviest sprints (likely split candidates): S2, S8, S10.

## Cadence
- Work is broken into tasks with a clear scope and a **Definition of Done**
  ([definition-of-done.md](../onboarding/definition-of-done.md)).
- Each task: build only what's scoped, validate (compile/boot/lint/YAML), update docs, then stop for
  review. Explicit "do not implement" lists are honored strictly.
- Backlogs live as spreadsheets (e.g. the Sprint 1 backlog) with tasks, subtasks, dependencies, DoD.

## Roles
Agent roles map to ownership in [`.github/CODEOWNERS`](../../.github/CODEOWNERS): product, business
analysis, solution/database architecture, backend, frontend, QA, DevOps, AI. Reviews route by area.

## Definition of Done (summary)
Tests/build green, lint/types clean, decisions respected, docs updated, and — for tenant data —
`organization_id` + RLS present. Full list: [definition-of-done.md](../onboarding/definition-of-done.md).
