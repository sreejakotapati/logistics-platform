# Git Workflow

Trunk-based development with short-lived branches and squash-merges. The contribution overview is in
[CONTRIBUTING](../../CONTRIBUTING.md); this is the mechanics.

## Branches
- `main` is always releasable and protected (no direct pushes, no force-push).
- Branch names: `feat/<scope>-<desc>`, `fix/<scope>-<desc>`, `chore/<scope>`, `docs/<scope>`,
  `refactor/<scope>`. Keep them short-lived; delete after merge.

## Commits — Conventional Commits
```
<type>(<scope>): <summary>

[body]
[BREAKING CHANGE: ...]
```
Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`, `build`. These drive the
changelog (`feat`→minor, `fix`→patch, `!`/`BREAKING CHANGE`→major post-1.0).

## Pull requests
1. Push your branch and open a PR; fill the [template](../../.github/pull_request_template.md).
2. CI runs the affected pipelines (path-filtered). Reviewers per CODEOWNERS approve.
3. Keep the branch up to date with `main` (rebase preferred). Resolve conversations.
4. **Squash-merge** — the PR title becomes the commit message; the branch is deleted.

## Keeping current
```bash
git fetch origin
git rebase origin/main      # preferred for a linear history
# resolve conflicts, then: git rebase --continue
```

## Releases
Cut from `main` by pushing a tag `vMAJOR.MINOR.PATCH`; `release.yml` generates GitHub Release notes.
Versioning rules: [release-and-versioning.md](release-and-versioning.md). Branch protection &
required checks: [ci-cd.md](ci-cd.md).
