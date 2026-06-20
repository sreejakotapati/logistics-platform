-- Bootstrap extensions (run once by the postgres superuser on container init).
-- No schema, roles, or tables here — only cluster/database extensions.

-- pgcrypto provides gen_random_bytes(), used by app.uuid_generate_v7().
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- NOTE: UUIDv7 is implemented in app.uuid_generate_v7() (PostgreSQL 16 has no native uuidv7).
-- NOTE: Row-Level Security is a built-in capability; no extension is required.
