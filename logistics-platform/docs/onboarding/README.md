# Getting Started

Goal: **clone to first contribution in ~30 minutes.** Each step lists a time budget; the long pole is
the first Docker image build.

## 0. Prerequisites (≈10 min, once)
- **Docker** + **Docker Compose v2**, and **Git**. Verify: `docker compose version`.
- Optional (for the fast inner loop): **Python 3.12**, **Node 20**.
- More detail and OS notes: [Setup Guide](../guides/setup.md).

## 1. Clone & configure (≈2 min)
```bash
git clone <repo-url> logistics-platform && cd logistics-platform
make env          # creates .env from .env.example
make env-check    # sanity-check required variables
```

## 2. Run the stack (≈10 min first time)
```bash
make up            # build + start postgres, redis, backend, frontend
# faster inner loop instead: make up-infra  (only db+redis), then run apps locally
```

## 3. Verify (≈3 min)
- http://localhost:3000 — app shell loads (sidebar, ⌘K command palette, theme toggle)
- http://localhost:8000/docs — API docs · `/health` returns ok · `/ready` returns 200 when db+redis are up
- `make ps` — every service is healthy

## 4. Run tests (≈2 min)
```bash
cd backend && pip install -r requirements-dev.txt && pytest
```

## 5. Make your first change (≈3 min)
```bash
git switch -c feat/<scope>-<short-desc>
# edit something; backend & frontend hot-reload in dev
```
Then read **[Contributing](../../CONTRIBUTING.md)** and **[Git Workflow](../guides/git-workflow.md)**
before opening a PR, and check the **[Definition of Done](definition-of-done.md)**.

## Orient yourself
- The six locked decisions you must respect: see the table in the [root README](../../README.md) and
  [ADR-0001](../adr/0001-foundation-architecture-decisions.md).
- Where things live: [Architecture Navigation Guide](../architecture/README.md).
- How we sequence work: [Sprint Process](../guides/sprint-process.md).
- Stuck? [Troubleshooting](../guides/troubleshooting.md).
