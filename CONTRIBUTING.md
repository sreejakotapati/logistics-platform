# Contributing

Thanks for contributing. This is the overview; mechanics live in linked guides.

## Before you start
1. Set up your environment: [Setup Guide](docs/guides/setup.md) → [Getting Started](docs/onboarding/README.md).
2. Understand the **locked decisions** (multi-tenancy, RLS, JWT active-org context, feature flags,
   notification abstraction, modular monolith): [ADR-0001](docs/adr/0001-foundation-architecture-decisions.md).
   Changing one requires a new ADR — see the [ADR Guide](docs/adr/README.md).

## Workflow
1. Branch from `main`: `feat/<scope>-<desc>`, `fix/<scope>-<desc>`, `chore/<scope>`, `docs/<scope>`.
2. Make focused changes. Keep modules within their boundaries (`router → service → repository`).
3. Run the same checks CI runs:
   - Backend: `ruff check . && mypy app && pytest`
   - Frontend: `npm run lint && npm run type-check && npm run build`
4. Commit using **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
   Details: [Git Workflow](docs/guides/git-workflow.md).
5. Open a PR, fill the template, and request review. CODEOWNERS routes reviewers by area.
6. Address review; **squash-merge**. The branch is deleted on merge.

## Definition of Done
A change is done when it meets the [Definition of Done](docs/onboarding/definition-of-done.md):
tests/build green, lint/types clean, docs updated, decisions respected, and (for tenant data)
RLS + `organization_id` in place.

## What CI enforces
Lint, type-checks, tests, image builds, and secret scanning are merge-blocking; coverage and
dependency/vuln scans run report-only in early sprints. See [CI/CD](docs/guides/ci-cd.md).

## Standards
Code style and naming: [Coding Standards](CONVENTIONS.md) and [Repository Standards](REPOSITORY_STANDARDS.md).
