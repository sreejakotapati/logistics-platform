# Environment Variable Strategy

## Principles
- **Single source of template:** `.env.example` is committed and always current. Every new variable
  is added there in the same PR (enforced by `REPOSITORY_STANDARDS.md`).
- **Real values are never committed:** `.env` is git-ignored. Secrets live only in `.env` locally and
  in a secret manager in staging/production.
- **12-factor:** all configuration comes from the environment; no hard-coded hosts, ports, or secrets.

## Layers & precedence (highest wins)
1. Process environment / orchestrator secrets (staging & production).
2. `docker-compose.override.yml` (personal local overrides, git-ignored).
3. `.env` (local values, git-ignored).
4. Defaults baked into `docker-compose.yml` (`${VAR:-default}`) and application settings.

## Who consumes what
| Consumer | Source | Notes |
|---|---|---|
| Docker Compose substitution (`${VAR}`) | root `.env` | auto-loaded; sets ports, image creds |
| Backend (FastAPI) | container env via `env_file: .env` | parsed by pydantic-settings (S1-T5) |
| Frontend (Next.js) | container env via `env_file: .env` | only `NEXT_PUBLIC_*` reach the browser |
| Postgres / Redis / MinIO images | container env | bootstrap default db/user, root creds |

## Naming
- `UPPER_SNAKE_CASE`. Browser-exposed frontend vars are prefixed `NEXT_PUBLIC_` (build-time, public).
- Group by domain in `.env.example`: App, Postgres, Redis, Auth/JWT, Storage, Notification providers,
  India-first compliance, Maps, Frontend, Local dev.

## Secrets handling
- Local: plain values in `.env` (low-risk dev credentials).
- Staging/Production: injected as secrets (e.g. orchestrator secret store / mounted files such as
  `FCM_CREDENTIALS_JSON_PATH`); never placed in `.env` files or images.

## Validation
- `make env` creates `.env` from the template if missing.
- `make env-check` (script `scripts/check-env.sh`) verifies required vars are present and not left as
  `change_me`.
