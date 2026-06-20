# Secrets

For **file-based secrets** in staging/production (git-ignored). Intentionally empty in the repo.

## Strategy (foundation)
- **Dev:** plain values in `.env` (low-risk dev credentials).
- **Staging:** `.env.staging`, `chmod 600`, never committed.
- **Production:** prefer a secret manager (e.g. Vault / platform secret store) or **Docker secrets**
  (file-mounted at `/run/secrets/<name>`) referenced by a `*_FILE` convention. The app will read
  `JWT_SECRET_FILE` / `*_FILE` variants (wired when the production deploy is built).

## Rules
- No secret values are committed. `.gitignore` excludes `.env.staging`, `.env.production`, `secrets/*`.
- Rotate per environment; staging and production never share secrets.
- CI uses GitHub Actions secrets; runtime secrets are injected by the host/orchestrator.
