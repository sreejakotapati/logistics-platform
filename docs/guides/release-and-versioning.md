# Branching, Release & Versioning Strategy

## Branching (trunk-based)
- `main` is always releasable and protected.
- Short-lived branches off `main`: `feat/<scope>-<desc>`, `fix/<scope>-<desc>`, `chore/<scope>`,
  `docs/<scope>`. Delete after merge. (Full rules: `CONTRIBUTING.md`, `CONVENTIONS.md`.)

## Pull-request workflow
1. Branch from `main`; commit using Conventional Commits.
2. Open a PR; fill the template (`.github/pull_request_template.md`).
3. CI runs the affected pipelines; reviewers per `CODEOWNERS` approve.
4. **Squash-merge** — the PR title becomes the conventional-commit message; the branch is deleted.

## Versioning (SemVer)
- Format `MAJOR.MINOR.PATCH`. The platform is in **0.x** during the build (pre-GA); breaking changes
  bump MINOR while < 1.0. GA is `1.0.0`.
- Source of truth: `backend/app/__init__.py` (`__version__`) and `frontend/package.json` (`version`)
  stay in lockstep.
- Conventional Commits drive the changelog: `feat` → minor, `fix` → patch, `feat!`/`BREAKING CHANGE`
  → major (post-1.0).

## Release strategy
- Releases are cut from `main` by pushing a tag `vMAJOR.MINOR.PATCH`.
- `release.yml` creates a **GitHub Release** with auto-generated notes from merged PRs.
- A pre-release tag (e.g. `v0.2.0-rc.1`) is marked prerelease automatically.
- **Deployment is intentionally not part of this foundation.** Image tagging (`sha-<short>`,
  `v<version>`) and environment deploys are defined in the deployment task.
