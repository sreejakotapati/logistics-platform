# Docker

Container definitions and compose stack. Authored in **S1-T2**.

- `backend/`, `frontend/` — service Dockerfiles.
- `postgres/`, `redis/` — init/config assets.
- Root `docker-compose.yml` orchestrates postgres, redis, backend, frontend (+ mailhog, minio for dev).
