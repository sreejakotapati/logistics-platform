"""RLS isolation suite (S2-T0) — proves tenant isolation before Sprint 2 tenant tables.

Maps to the RLS Verification Plan (requirements A–J). Subject roles:
  app_conn   = app_user          (runtime role; must be fully constrained)
  super_conn = app_superadmin     (approved BYPASSRLS — controlled exception)
  owner_conn = logistics_migrator (owns the probe; constrained by FORCE RLS)
"""
from __future__ import annotations

import psycopg
import pytest

pytestmark = pytest.mark.integration

TBL = "rls_verify.tenant_probe"


# ---- helpers ---------------------------------------------------------------
def _set_org(cur, org):
    # SET LOCAL cannot be parameterized; set_config(..., is_local=true) is the transaction-local form.
    cur.execute("SELECT set_config('app.current_org_id', %s, true)", (org,))


def count(conn, org="__unset__"):
    with conn.cursor() as cur:
        if org != "__unset__":
            _set_org(cur, org)
        cur.execute(f"SELECT count(*) FROM {TBL}")
        return cur.fetchone()[0]


# ---- L0 structural ---------------------------------------------------------
def test_s1_rls_enabled_and_forced(probe, admin_conn):
    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid=%s::regclass",
            (TBL,),
        )
        assert cur.fetchone() == (True, True)


def test_s2_policy_present_with_using_and_check(probe, admin_conn):
    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT polname::text, pg_get_expr(polqual, polrelid), pg_get_expr(polwithcheck, polrelid) "
            "FROM pg_policy WHERE polrelid=%s::regclass",
            (TBL,),
        )
        rows = cur.fetchall()
    assert len(rows) == 1
    def _s(v):
        return v.decode() if isinstance(v, (bytes, bytearray)) else v
    name, using, withcheck = (_s(x) for x in rows[0])
    assert name == "org_isolation"
    assert "current_org_id" in using and "current_org_id" in withcheck


# ---- L1 positive isolation (A, B, J) --------------------------------------
def test_a_org_a_sees_only_its_rows(probe, app_conn):
    assert count(app_conn, probe["org_a"]) == 3


def test_a_org_a_cannot_read_b_row(probe, app_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_a"])
        cur.execute(f"SELECT count(*) FROM {TBL} WHERE id=%s", (probe["b_id"],))
        assert cur.fetchone()[0] == 0


def test_b_org_b_sees_only_its_rows(probe, app_conn):
    assert count(app_conn, probe["org_b"]) == 2


def test_b_org_b_cannot_read_a_row(probe, app_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_b"])
        cur.execute(f"SELECT count(*) FROM {TBL} WHERE id=%s", (probe["a_id"],))
        assert cur.fetchone()[0] == 0


# ---- L2 cross-tenant DML (F, G, H) ----------------------------------------
def test_f_cross_tenant_insert_rejected(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            _set_org(cur, probe["org_a"])
            cur.execute(
                f"INSERT INTO {TBL} (organization_id, payload) VALUES (%s,'A-injects-B')",
                (probe["org_b"],),
            )


def test_f_same_org_insert_allowed(probe, app_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_a"])
        cur.execute(
            f"INSERT INTO {TBL} (organization_id, payload) VALUES (%s,'A-4')", (probe["org_a"],)
        )
        cur.execute(f"SELECT count(*) FROM {TBL}")
        assert cur.fetchone()[0] == 4  # rolled back by teardown


def test_g_targeted_cross_update_is_noop(probe, app_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_a"])
        cur.execute(f"UPDATE {TBL} SET payload='x' WHERE id=%s", (probe["b_id"],))
        assert cur.rowcount == 0


def test_g_blind_update_scoped_to_own_org(probe, app_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_a"])
        cur.execute(f"UPDATE {TBL} SET payload='x'")
        assert cur.rowcount == 3  # only A's rows


def test_g_retenant_update_rejected(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            _set_org(cur, probe["org_a"])
            cur.execute(
                f"UPDATE {TBL} SET organization_id=%s WHERE id=%s",
                (probe["org_b"], probe["a_id"]),
            )


def test_h_targeted_cross_delete_is_noop(probe, app_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_a"])
        cur.execute(f"DELETE FROM {TBL} WHERE id=%s", (probe["b_id"],))
        assert cur.rowcount == 0


def test_h_blind_delete_scoped_to_own_org(probe, app_conn, super_conn):
    with app_conn.cursor() as cur:
        _set_org(cur, probe["org_a"])
        cur.execute(f"DELETE FROM {TBL}")
        assert cur.rowcount == 3  # B's rows untouched
    # B rows still present (the delete is uncommitted; survivor check via bypass role)
    assert count(super_conn) == 5


# ---- L3 context safety (D, E) ---------------------------------------------
def test_d_missing_context_returns_no_rows(probe, app_conn):
    with app_conn.cursor() as cur:
        cur.execute("SELECT app.current_org_id()")
        assert cur.fetchone()[0] is None
        cur.execute(f"SELECT count(*) FROM {TBL}")
        assert cur.fetchone()[0] == 0


def test_d_missing_context_insert_rejected(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {TBL} (organization_id, payload) VALUES (%s,'orphan')",
                (probe["org_a"],),
            )


def test_e_empty_context_returns_no_rows(probe, app_conn):
    assert count(app_conn, "") == 0


def test_e_invalid_uuid_context_errors(probe, app_conn):
    with pytest.raises(psycopg.errors.InvalidTextRepresentation):
        with app_conn.cursor() as cur:
            _set_org(cur, "not-a-uuid")
            cur.execute(f"SELECT count(*) FROM {TBL}")


def test_e_unknown_org_returns_no_rows(probe, app_conn):
    assert count(app_conn, probe["org_c"]) == 0


# ---- L4 bypass resistance (C, J) ------------------------------------------
def test_c_row_security_off_cannot_bypass(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute("SET LOCAL row_security = off")
            cur.execute(f"SELECT count(*) FROM {TBL}")


def test_c_app_user_cannot_disable_rls(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute(f"ALTER TABLE {TBL} DISABLE ROW LEVEL SECURITY")


def test_c_app_user_cannot_drop_policy(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute(f"DROP POLICY org_isolation ON {TBL}")


def test_c_app_user_cannot_escalate_via_set_role(probe, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute("SET ROLE app_superadmin")


def test_j_app_user_role_attributes(probe, admin_conn):
    with admin_conn.cursor() as cur:
        cur.execute(
            "SELECT rolsuper, rolbypassrls, rolcanlogin FROM pg_roles WHERE rolname='app_user'"
        )
        assert cur.fetchone() == (False, False, True)


# ---- L5 approved bypass & FORCE (I, J) ------------------------------------
def test_i_superadmin_bypass_sees_all(probe, super_conn):
    assert count(super_conn) == 5  # no context, all orgs visible


def test_j_owner_is_constrained_by_force(probe, owner_conn):
    assert count(owner_conn) == 0  # owner, no context -> FORCE RLS blocks
    assert count(owner_conn, probe["org_a"]) == 3
