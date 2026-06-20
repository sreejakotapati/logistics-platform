# Infrastructure Architecture (Staging Foundation)

Cloud-agnostic: the whole stack runs with Docker Compose on any Linux host (VM, bare metal, or a
managed VM on any cloud). No provider-specific services are used; moving to a managed platform later
is additive.

## Topology
```mermaid
flowchart TD
  user[Browser / API client] -->|HTTPS 443| caddy[Caddy reverse proxy]
  caddy -->|/, static| fe[Next.js (standalone)]
  caddy -->|/api/*, /health, /docs| be[FastAPI]
  be --> pg[(PostgreSQL 16)]
  be --> rd[(Redis 7)]
  subgraph internal network (not published)
    fe
    be
    pg
    rd
  end
  caddy ---|edge network| internet
```

## Environments
| | Compose file | Domain | Exposed ports | TLS |
|---|---|---|---|---|
| Development | `docker-compose.yml` | `localhost` | DB/Redis/app on host | none |
| Staging | `docker-compose.staging.yml` | `STAGING_DOMAIN` | 80/443 only (proxy) | Caddy auto / internal |
| Production | same staging file + `.env.production` | `app.<domain>` | 80/443 only | Caddy auto (LE) |

## Networks & volumes
- **edge** — public, only Caddy attaches (80/443). **internal** — app + data tier; **no host ports**
  for Postgres/Redis in staging/production.
- Named volumes: `pgdata`, `redisdata`, `caddy_data` (certs), `caddy_config`. Monitoring/logging add
  `prometheus_data`, `grafana_data`, `loki_data`.

## Optional overlays
- **Monitoring:** `docker-compose.monitoring.yml` (Prometheus, cAdvisor, node-exporter, Grafana).
- **Logging:** `docker-compose.logging.yml` (Loki + Promtail).

## Not in this foundation
No cloud-specific deployment (no AWS/Azure/GCP services, no managed DB, no load balancer, no IaC).
Those are a later task; this foundation is the portable baseline they build on.
