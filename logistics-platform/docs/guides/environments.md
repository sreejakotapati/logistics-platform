# Environments: Development · Staging · Production

Three environments share one codebase and image build; they differ only in configuration.

## Configuration matrix
| Aspect | Development | Staging | Production |
|---|---|---|---|
| Config source | `.env` (committed example) | `.env.staging` (git-ignored) | `.env.production` + secret manager |
| `APP_ENV` / debug | `local` / on | `staging` / off | `production` / off |
| Log level | debug/info | info | warning |
| Domain | `localhost` | `staging.<domain>` | `app.<domain>` |
| TLS | none | Caddy (auto/internal) | Caddy (Let's Encrypt) |
| DB/Redis host ports | published | **not published** | **not published** |
| Secrets | dev placeholders | strong, rotated | secret manager / Docker secrets |
| Backups | none | scheduled pg_dump | scheduled + offsite |

## Secrets management
- Dev placeholders only in `.env`. Staging/production secrets are never committed.
- `.gitignore` blocks `.env.staging`, `.env.production`, `secrets/*`. `.env.*.example` templates are
  tracked. Set `chmod 600` on real env files. See `secrets/README.md` for the Docker-secrets path.

## Domain & SSL/TLS strategy
- One domain per environment (`staging.<domain>`, `app.<domain>`). DNS A/AAAA record points at the
  Docker host; Caddy terminates TLS and reverse-proxies to the frontend/backend.
- **Public domain:** Caddy provisions and auto-renews Let's Encrypt certificates. **No public DNS:**
  set `STAGING_DOMAIN=staging.localhost` and enable `tls internal` (self-signed) in the Caddyfile.
- HSTS and security headers are set at the proxy.

## Promotion flow
`dev (compose up)` → `staging (deploy-staging.sh)` → `production (same compose, .env.production)`.
Image build is identical across environments; only env/secrets change.
