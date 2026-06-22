"""Fixtures for the RLS isolation suite (S2-T0).

Implements the approved RLS Verification Plan. Uses a single ephemeral probe table in a throwaway
`rls_verify` schema (created/seeded/dropped here) — NO business tables. Connects under three distinct
roles so RLS behavior is observed for the runtime role (`app_user`), the approved bypass role
(`app_superadmin`), and the table owner (`logistics_migrator`, constrained by FORCE RLS).

The whole suite is skipped unless `RLS_ADMIN_DSN` points at a reachable PostgreSQL with the `app`
schema (created by `alembic upgrade head`). CI provides it; local runs without a DB skip cleanly.
"""
from __future__ import annotations

import os

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg.conninfo import conninfo_to_dict, make_conninfo  # noqa: E402

# Fixed test identities (deterministic; asymmetric seed makes any leak observable).
ORG_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
ORG_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ORG_C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"  # valid UUID, no rows

APP_PW = "test_app_pw"
MIG_PW = "test_mig_pw"
SA_PW = "test_sa_pw"


def _admin_dsn() -> str | None:
    dsn = os.environ.get("RLS_ADMIN_DSN")
    if not dsn:
        return None
    return dsn.replace("postgresql+psycopg://", "postgresql://")


def _role_dsn(base: dict, user: str, password: str) -> str:
    return make_conninfo(
        host=base.get("host", "localhost"),
        port=base.get("port", "5432"),
        dbname=base.get("dbname"),
        user=user,
        password=password,
    )


@pytest.fixture(scope="session")
def base_info() -> dict:
    dsn = _admin_dsn()
    if not dsn:
        pytest.skip("RLS_ADMIN_DSN not set — skipping RLS integration suite")
    try:
        return conninfo_to_dict(dsn)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"invalid RLS_ADMIN_DSN: {exc}")


@pytest.fixture(scope="session")
def admin_conn(base_info):
    try:
        conn = psycopg.connect(make_conninfo(**base_info), autocommit=True)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"cannot connect as admin: {exc}")
    # The app schema/functions must already exist (alembic upgrade head).
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_namespace WHERE nspname='app'")
        if cur.fetchone() is None:
            pytest.skip("`app` schema absent — run `alembic upgrade head` first")
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def provisioned(admin_conn):
    """Create the three test roles (idempotent) and grant them access to the `app` functions."""
    roles = [
        ("app_user", APP_PW, "NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB"),
        ("logistics_migrator", MIG_PW, "NOSUPERUSER NOBYPASSRLS"),
        ("app_superadmin", SA_PW, "NOSUPERUSER BYPASSRLS"),
    ]
    with admin_conn.cursor() as cur:
        for name, pw, attrs in roles:
            cur.execute(
                f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{name}') "
                f"THEN CREATE ROLE {name} LOGIN; END IF; END $$;"
            )
            cur.execute(f"ALTER ROLE {name} LOGIN PASSWORD '{pw}' {attrs};")
        cur.execute(
            "GRANT USAGE ON SCHEMA app TO app_user, logistics_migrator, app_superadmin;"
        )
        cur.execute(
            "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app "
            "TO app_user, logistics_migrator, app_superadmin;"
        )
        # public business tables (real Sprint-2 tables): app_user created after migrations in CI,
        # so grant here. Full DML lets the isolation tests exercise every RLS path; append-only and
        # grant-level restrictions are asserted separately.
        cur.execute("GRANT USAGE ON SCHEMA public TO app_user, app_superadmin;")
        cur.execute(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
            "TO app_user, app_superadmin;"
        )
    yield


@pytest.fixture(scope="session")
def probe(provisioned, admin_conn, base_info):
    """Ephemeral probe table owned by the migrator, seeded A×3/B×2, then RLS-enabled."""
    # Owner = migrator (non-superuser) so FORCE-RLS-on-owner is meaningful.
    with admin_conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS rls_verify CASCADE;")
        cur.execute("CREATE SCHEMA rls_verify AUTHORIZATION logistics_migrator;")

    mig = psycopg.connect(_role_dsn(base_info, "logistics_migrator", MIG_PW), autocommit=True)
    with mig.cursor() as cur:
        cur.execute("GRANT USAGE ON SCHEMA rls_verify TO app_user, app_superadmin;")
        cur.execute(
            "CREATE TABLE rls_verify.tenant_probe ("
            " id uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),"
            " organization_id uuid NOT NULL,"
            " payload text NOT NULL,"
            " created_at timestamptz NOT NULL DEFAULT now());"
        )
        cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON rls_verify.tenant_probe TO app_user;")
        cur.execute("GRANT SELECT ON rls_verify.tenant_probe TO app_superadmin;")
        # Seed BEFORE enabling RLS so seeding isn't blocked by the policy.
        cur.execute(
            "INSERT INTO rls_verify.tenant_probe (organization_id, payload) VALUES "
            "(%s,'A-1'),(%s,'A-2'),(%s,'A-3'),(%s,'B-1'),(%s,'B-2')",
            (ORG_A, ORG_A, ORG_A, ORG_B, ORG_B),
        )
        cur.execute("SELECT id FROM rls_verify.tenant_probe WHERE organization_id=%s LIMIT 1", (ORG_A,))
        a_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM rls_verify.tenant_probe WHERE organization_id=%s LIMIT 1", (ORG_B,))
        b_id = cur.fetchone()[0]
        cur.execute("SELECT app.enable_org_rls('rls_verify.tenant_probe');")

    yield {"a_id": a_id, "b_id": b_id, "org_a": ORG_A, "org_b": ORG_B, "org_c": ORG_C}

    mig.close()
    with admin_conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS rls_verify CASCADE;")


def _conn(base_info, user, pw):
    return psycopg.connect(_role_dsn(base_info, user, pw))  # autocommit=False (transactional)


@pytest.fixture(scope="session")
def app_conn(provisioned, base_info):
    c = _conn(base_info, "app_user", APP_PW)
    yield c
    c.close()


@pytest.fixture(scope="session")
def super_conn(provisioned, base_info):
    c = _conn(base_info, "app_superadmin", SA_PW)
    yield c
    c.close()


@pytest.fixture(scope="session")
def owner_conn(provisioned, base_info):
    c = _conn(base_info, "logistics_migrator", MIG_PW)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def _rollback_after(app_conn, super_conn, owner_conn):
    """Each test runs in its own transaction; roll back so mutations never persist."""
    yield
    for c in (app_conn, super_conn, owner_conn):
        try:
            c.rollback()
        except Exception:  # noqa: BLE001
            pass
