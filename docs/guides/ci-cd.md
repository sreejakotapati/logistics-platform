# CI/CD (Foundation)

GitHub Actions runs on every pull request and on pushes to `main`. **No deployment runs in this
foundation** — image push and environment deploys are a later task.

## Workflows
| Workflow | Trigger | What it does |
|---|---|---|
| `backend-ci.yml` | PR/push touching backend, database, backend docker | Ruff + Mypy; pytest with **Postgres + Redis service containers**; applies the Alembic foundation migration |
| `frontend-ci.yml` | PR/push touching frontend | `npm lint` + `type-check` + `build` |
| `docker-build.yml` | PR/push touching code or docker | Builds the **production** backend & frontend images (no push) |
| `security.yml` | PR/push + weekly | CodeQL (python + JS/TS), Trivy fs scan, gitleaks secret scan |
| `dependency-scan.yml` | PR/push touching manifests + weekly | pip-audit + npm audit |
| `release.yml` | tag `v*.*.*` | Creates a GitHub Release with generated notes (no deploy) |

Path filters keep PRs fast — only the affected pipelines run. `concurrency` cancels superseded runs.

## Gate policy (S1 vs later)
- **Hard gates now:** lint, type-check, tests, image builds, **secret scan (gitleaks)**.
- **Report-only now (tighten in Sprint 2):** coverage `--cov-fail-under=80`, Trivy `exit-code 1`,
  pip-audit/npm audit gating. Each is wired and runs; it simply does not fail the build yet, because
  the foundation has little exercised code and unvetted transitive deps.

## Repository protection strategy
Protect `main`:
- Require a pull request with **≥1 approving review**; dismiss stale approvals on new commits.
- Require these **status checks** to pass before merge:
  `Backend Lint & Types`, `Backend Tests`, `Frontend Lint, Types & Build`,
  `Build backend image`, `Build frontend image`, `Secret scan (gitleaks)`.
- Require branches to be **up to date** before merging; require **linear history** (squash-merge).
- **No direct pushes** to `main`; no force-pushes.
- **CODEOWNERS** (`.github/CODEOWNERS`) routes reviews to the owning agent/role.

## Environment strategy
- **CI** uses ephemeral service containers (Postgres, Redis) — no shared infrastructure.
- GitHub **Environments** `staging` and `production` are **reserved** for the deployment task; their
  secrets (DB URLs, provider credentials, registry tokens) will be scoped per environment and never
  placed in the repo. No deploy job exists yet.
- Secrets used by CI live in GitHub Actions secrets; nothing sensitive is committed (enforced by
  gitleaks + `.gitignore`).
