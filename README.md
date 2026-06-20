# Logistics Management Platform

Enterprise, multi-tenant SaaS for logistics operations — India-first (GSTIN, GST, e-way bill, INR),
built as a **modular monolith** with a FastAPI backend and a Next.js 15 frontend.

> **Status:** Sprint 1 (Foundations) complete. The app shell runs; business modules begin in Sprint 2.
> New here? Start with **[Getting Started](docs/onboarding/README.md)** — clone to first contribution
> in ~30 minutes.

---

## Quickstart (≈30 minutes)

**Prerequisites:** Docker + Docker Compose v2, Git. (Optional for the fast inner loop: Python 3.12,
Node 20.) Full details: **[Setup Guide](docs/guides/setup.md)**.

```bash
git clone <repo-url> logistics-platform && cd logistics-platform
make env            # copy .env.example -> .env
make up             # build + start postgres, redis, backend, frontend  (first build pulls images)
```
Then open:
- Frontend — http://localhost:3000
- API docs — http://localhost:8000/docs
- Liveness — http://localhost:8000/health · Readiness — http://localhost:8000/ready

Faster inner loop (skip image builds): `make up-infra` (Postgres + Redis only), then run the
backend and frontend locally — see the **[Local Development Guide](docs/guides/local-development.md)**.

Verify and start contributing:
```bash
make ps                              # all services healthy
cd backend && pytest                 # backend tests pass
git switch -c feat/<scope>-<desc>    # branch, then edit with hot reload
```

---

## Core architecture (locked decisions)

These are settled and recorded in **[ADR-0001](docs/adr/0001-foundation-architecture-decisions.md)**.
Don't reopen them without a new ADR (**[ADR Guide](docs/adr/README.md)**).

| Decision | Summary | Where |
|---|---|---|
| **Multi-tenancy** | Shared schema + `organization_id`, isolation enforced in the database | [multi-tenancy](docs/architecture/multi-tenancy.md) |
| **PostgreSQL RLS** | Row-Level Security on every tenant table; runtime role can't bypass it | [multi-tenancy](docs/architecture/multi-tenancy.md) · [database](docs/architecture/database-architecture.md) |
| **JWT active-organization context** | Active org is a signed JWT claim that sets the RLS context per request; switching mints a new token (never a client header) | [ADR-0001](docs/adr/0001-foundation-architecture-decisions.md) · [backend](docs/architecture/backend-architecture.md) |
| **Feature flags** | Capabilities toggled by config (per org/environment), not code branches | [ADR-0001](docs/adr/0001-foundation-architecture-decisions.md) |
| **Notification provider abstraction** | Email/SMS/WhatsApp/Push behind provider interfaces; adapter = config, not code | [ADR-0001](docs/adr/0001-foundation-architecture-decisions.md) |
| **Modular monolith** | One deployable; clear module boundaries (`router → service → repository`) | [backend](docs/architecture/backend-architecture.md) |

Full map: **[Architecture Navigation Guide](docs/architecture/README.md)**.

---

## Repository layout
```
backend/      FastAPI (modular monolith) · SQLAlchemy 2 async · Alembic
frontend/     Next.js 15 (App Router) · TypeScript · Tailwind · ShadCN
database/     init scripts (extensions, roles) — no business tables in S1
docker/       Dockerfiles, Caddy, Redis, Prometheus/Loki/Promtail configs
docs/         architecture · guides · adr · onboarding · runbooks
scripts/      deploy-staging.sh · backup-postgres.sh · check-env.sh
.github/      CI/CD workflows, CODEOWNERS, dependabot
```

## Documentation
Everything is indexed in **[docs/README.md](docs/README.md)**. Most-used:
[Getting Started](docs/onboarding/README.md) ·
[Setup](docs/guides/setup.md) ·
[Local Development](docs/guides/local-development.md) ·
[Contributing](CONTRIBUTING.md) ·
[Coding Standards](CONVENTIONS.md) ·
[Git Workflow](docs/guides/git-workflow.md) ·
[Sprint Process](docs/guides/sprint-process.md) ·
[Troubleshooting](docs/guides/troubleshooting.md)

## Tooling
`make help` lists all targets (dev, staging, monitoring, logging, backup). CI runs lint, type-checks,
tests, image builds, and security scans on every PR — see **[CI/CD](docs/guides/ci-cd.md)**.

## License
See [LICENSE](LICENSE).
