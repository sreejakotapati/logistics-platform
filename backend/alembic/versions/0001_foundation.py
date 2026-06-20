"""foundation: app schema, UUIDv7, tenancy + RLS helpers, grants

Revision ID: 0001_foundation
Revises:
Create Date: 2026-06-20

Establishes the database FOUNDATION only. NO business or entity tables are created here
(organizations, users, etc. are Sprint-2 module work). This migration provides:
  * the `app` schema
  * app.uuid_generate_v7()      — UUIDv7 primary-key generator
  * app.current_org_id()        — reads the per-request active org from a GUC (set from the JWT)
  * app.set_updated_at()        — trigger function for updated_at maintenance
  * app.enable_org_rls(regclass)— applies the standard tenant-isolation policy to a table
  * runtime grants + default privileges so future tables are usable by the app role
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0001_foundation"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app;")

    # --- UUIDv7 generator (PostgreSQL 16 has no native uuidv7) ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.uuid_generate_v7()
        RETURNS uuid
        LANGUAGE plpgsql
        VOLATILE
        AS $func$
        DECLARE
            unix_ts_ms bigint;
            b bytea;
        BEGIN
            unix_ts_ms := (extract(epoch from clock_timestamp()) * 1000)::bigint;
            b := gen_random_bytes(16);
            -- 48-bit big-endian timestamp in the first 6 bytes
            b := set_byte(b, 0, ((unix_ts_ms >> 40) & 255)::int);
            b := set_byte(b, 1, ((unix_ts_ms >> 32) & 255)::int);
            b := set_byte(b, 2, ((unix_ts_ms >> 24) & 255)::int);
            b := set_byte(b, 3, ((unix_ts_ms >> 16) & 255)::int);
            b := set_byte(b, 4, ((unix_ts_ms >> 8) & 255)::int);
            b := set_byte(b, 5, (unix_ts_ms & 255)::int);
            -- version 7 in the high nibble of byte 6
            b := set_byte(b, 6, ((get_byte(b, 6) & 15) | 112));
            -- RFC 4122 variant in the top two bits of byte 8
            b := set_byte(b, 8, ((get_byte(b, 8) & 63) | 128));
            RETURN encode(b, 'hex')::uuid;
        END;
        $func$;
        """
    )

    # --- Active-organization context (set per request from the JWT claim) ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.current_org_id()
        RETURNS uuid
        LANGUAGE sql
        STABLE
        AS $func$
            SELECT NULLIF(current_setting('app.current_org_id', true), '')::uuid;
        $func$;
        """
    )

    # --- updated_at trigger function (attached per table in later migrations) ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $func$
        BEGIN
            NEW.updated_at := now();
            RETURN NEW;
        END;
        $func$;
        """
    )

    # --- Reusable tenant-isolation enabler (called by every org-scoped table migration) ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app.enable_org_rls(target regclass)
        RETURNS void
        LANGUAGE plpgsql
        AS $func$
        BEGIN
            EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', target::text);
            EXECUTE format('ALTER TABLE %s FORCE ROW LEVEL SECURITY', target::text);
            EXECUTE format(
                'CREATE POLICY org_isolation ON %s '
                'USING (organization_id = app.current_org_id()) '
                'WITH CHECK (organization_id = app.current_org_id())',
                target::text
            );
        END;
        $func$;
        """
    )

    # --- Grants + default privileges so app_user can use future objects ---
    op.execute(
        """
        DO $grants$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                GRANT USAGE ON SCHEMA app TO app_user;
                GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO app_user;
                GRANT USAGE ON SCHEMA public TO app_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA app
                    GRANT EXECUTE ON FUNCTIONS TO app_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
                ALTER DEFAULT PRIVILEGES IN SCHEMA public
                    GRANT USAGE, SELECT ON SEQUENCES TO app_user;
            END IF;
        END
        $grants$;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS app.enable_org_rls(regclass);")
    op.execute("DROP FUNCTION IF EXISTS app.set_updated_at();")
    op.execute("DROP FUNCTION IF EXISTS app.current_org_id();")
    op.execute("DROP FUNCTION IF EXISTS app.uuid_generate_v7();")
    op.execute("DROP SCHEMA IF EXISTS app CASCADE;")
