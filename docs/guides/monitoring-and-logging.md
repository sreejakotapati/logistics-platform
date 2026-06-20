# Monitoring & Logging Foundation

## Health checks (strategy)
Layered, so a failure is localized:
- **Container** — Compose healthchecks: Postgres `pg_isready`, Redis `redis-cli ping`, backend
  `/health`, frontend root. Unhealthy containers are visible in `docker ps` and gate `depends_on`.
- **Application** — `/health` (liveness, no deps) and `/ready` (checks DB + Redis, 503 if degraded).
- **Edge** — the reverse proxy fronts both; an external uptime monitor should poll
  `https://<domain>/health` and alert.
- **Deploy** — `deploy-staging.sh` blocks on `/ready` before declaring success.

## Monitoring foundation
`docker-compose.monitoring.yml` brings up:
- **Prometheus** (scrape/store), **cAdvisor** (per-container CPU/mem/IO), **node-exporter** (host),
  **Grafana** (dashboards). Admin ports bind to `127.0.0.1` only.
- **Now:** container + host metrics. **Sprint 9:** the FastAPI app exposes `/metrics`; uncomment the
  `backend` scrape job and attach this stack to the staging `internal` network.

## Logging foundation
- The backend already emits **structured JSON logs** to stdout with a `request_id`; Docker captures
  stdout/stderr.
- **Rotation:** the staging compose sets the `json-file` driver with `max-size 10m`, `max-file 5` per
  service, so disk usage is bounded without extra infrastructure.
- **Aggregation (optional):** `docker-compose.logging.yml` runs **Loki + Promtail**; Promtail tails
  container logs and ships them to Loki, queryable in Grafana (add a Loki datasource at
  `http://loki:3100`). Retention defaults to 7 days.
