# Repository Standards

## Monorepo principles
- One repository, clear top-level boundaries (`frontend`, `backend`, `database`, `integrations`,
  `ai-services`, `docker`, `scripts`, `tests`, `docs`).
- No cross-boundary reaching except through defined interfaces/contracts.

## Ownership (maps folders to agents)
| Area | Owner agent |
|---|---|
| `backend/` | backend-engineer |
| `frontend/` | frontend-engineer |
| `database/`, migrations, RLS | database-architect |
| `integrations/notifications`, providers | backend-engineer (config: devops-engineer) |
| `ai-services/` | ai-engineer |
| `docker/`, `.github/workflows`, env, releases | devops-engineer |
| `docs/architecture`, `docs/adr` | solution-architect |
| `tests/` (isolation/e2e) | qa-engineer |

## Branch protection
- `main` protected: PR required, ≥1 approval, all CI checks green, up-to-date branch.
- No direct pushes to `main`. Linear history (squash-merge).

## CI gates (merge blockers, from S1-T7)
- Lint, type-check, unit/integration tests, build — for both frontend and backend.
- Coverage gate (≥80% target). Docker build validation.

## Security
- No secrets in the repo. `.env` is git-ignored; `.env.example` is kept current.
- Provider credentials (SES, MSG91, WhatsApp, FCM) injected via environment/secrets only.
- Dependency scanning runs in CI; flagged criticals block release.

## Multi-tenancy (non-negotiable)
- Every business table carries `organization_id`; RLS is enabled from the first migration.
- Active organization comes only from the signed JWT claim (locked decision #1) — never a client header.
- A missing tenant filter is a release-blocking defect.

## Testing
- Tests live with their code (`backend/tests`, frontend co-located); cross-cutting e2e and the
  tenant-isolation suite live in `tests/`.
- No task is Done without its tests; flaky tests are quarantined and fixed, not ignored.

## Documentation & decisions
- Significant or irreversible decisions are recorded as ADRs in `docs/adr/` (template: `0000`).
- READMEs explain each top-level folder's purpose and the sprint/task that populates it.

## Definition of Done
- See `docs/onboarding` and the Sprint backlog DoD; the PR template encodes the per-change checklist.
