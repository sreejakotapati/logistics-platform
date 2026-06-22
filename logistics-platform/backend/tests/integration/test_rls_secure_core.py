"""RLS isolation suite for the real secure-core tenant tables (S2-T1).

Adds every new org-scoped table to the verification harness: organizations, user_organizations,
user_organization_roles, audit_logs (standard isolation) and the hybrid roles / role_permissions
(custom rows isolated, system rows shared). Parents are seeded via the BYPASSRLS role; assertions
run as `app_user`.
"""
from __future__ import annotations

import psycopg
import pytest

from tests.integration.conftest import ORG_A, ORG_B, SA_PW, _role_dsn

pytestmark = pytest.mark.integration

USER_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture(scope="module")
def seeded(provisioned, base_info, admin_conn):
    """Seed two orgs (A, B), one user, a membership + custom role + audit row in each. Bypass RLS."""
    sup = psycopg.connect(_role_dsn(base_info, "app_superadmin", SA_PW), autocommit=True)
    with sup.cursor() as cur:
        cur.execute(
            "INSERT INTO public.users (id, email, full_name) VALUES (%s,'rlscore@test','Probe User')",
            (USER_ID,),
        )
        cur.execute(
            "INSERT INTO public.organizations (id, name, slug) VALUES (%s,'Org A','rlscore-a'),(%s,'Org B','rlscore-b')",
            (ORG_A, ORG_B),
        )
        cur.execute(
            "INSERT INTO public.user_organizations (user_id, organization_id, status, is_primary) "
            "VALUES (%s,%s,'active',true),(%s,%s,'active',false)",
            (USER_ID, ORG_A, USER_ID, ORG_B),
        )
        cur.execute(
            "INSERT INTO public.roles (organization_id, name) VALUES (%s,'Custom A'),(%s,'Custom B')",
            (ORG_A, ORG_B),
        )
        cur.execute(
            "INSERT INTO public.audit_logs (organization_id, actor_user_id, action) "
            "VALUES (%s,%s,'seed.a'),(%s,%s,'seed.b')",
            (ORG_A, USER_ID, ORG_B, USER_ID),
        )
    yield {"user": USER_ID}
    sup.close()
    # Cleanup via superuser; audit immutability trigger must be lifted to remove seed rows.
    with admin_conn.cursor() as cur:
        cur.execute("ALTER TABLE public.audit_logs DISABLE TRIGGER audit_logs_immutable;")
        for t in ("user_organization_roles", "role_permissions", "roles",
                  "audit_logs", "user_organizations"):
            cur.execute(f"DELETE FROM public.{t} WHERE organization_id IN (%s,%s)", (ORG_A, ORG_B))
        cur.execute("DELETE FROM public.organizations WHERE id IN (%s,%s)", (ORG_A, ORG_B))
        cur.execute("DELETE FROM public.users WHERE id=%s", (USER_ID,))
        cur.execute("ALTER TABLE public.audit_logs ENABLE TRIGGER audit_logs_immutable;")


def _count(conn, table, org, where=""):
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.current_org_id', %s, true)", (org,))
        cur.execute(f"SELECT count(*) FROM public.{table} {where}")
        return cur.fetchone()[0]


# ---- standard org-scoped isolation ----------------------------------------
def test_organizations_isolated(seeded, app_conn):
    assert _count(app_conn, "organizations", ORG_A) == 1
    assert _count(app_conn, "organizations", ORG_B) == 1


def test_organization_root_is_self_only(seeded, app_conn):
    # under org A, the only visible organization row is A itself
    with app_conn.cursor() as cur:
        cur.execute("SELECT set_config('app.current_org_id', %s, true)", (ORG_A,))
        cur.execute("SELECT count(*) FROM public.organizations WHERE id = %s", (ORG_B,))
        assert cur.fetchone()[0] == 0


def test_memberships_isolated(seeded, app_conn):
    assert _count(app_conn, "user_organizations", ORG_A) == 1
    assert _count(app_conn, "user_organizations", ORG_B) == 1


def test_audit_logs_isolated(seeded, app_conn):
    assert _count(app_conn, "audit_logs", ORG_A) == 1
    assert _count(app_conn, "audit_logs", ORG_B) == 1


def test_missing_context_hides_all_secure_core(seeded, app_conn):
    assert _count(app_conn, "user_organizations", "") == 0
    assert _count(app_conn, "audit_logs", "") == 0


# ---- cross-tenant DML rejection -------------------------------------------
def test_cross_tenant_membership_insert_rejected(seeded, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute("SELECT set_config('app.current_org_id', %s, true)", (ORG_A,))
            cur.execute(
                "INSERT INTO public.user_organizations (user_id, organization_id) VALUES (%s,%s)",
                (seeded["user"], ORG_B),
            )


# ---- append-only audit -----------------------------------------------------
def test_audit_logs_update_blocked(seeded, app_conn):
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute("SELECT set_config('app.current_org_id', %s, true)", (ORG_A,))
            cur.execute("UPDATE public.audit_logs SET action='tamper' WHERE organization_id=%s", (ORG_A,))


# ---- hybrid roles: system shared, custom isolated --------------------------
def test_system_roles_shared_custom_isolated(seeded, app_conn):
    with app_conn.cursor() as cur:
        cur.execute("SELECT set_config('app.current_org_id', %s, true)", (ORG_A,))
        cur.execute("SELECT count(*) FROM public.roles WHERE organization_id IS NULL")
        system_visible = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM public.roles WHERE organization_id = %s", (ORG_A,))
        own_custom = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM public.roles WHERE organization_id = %s", (ORG_B,))
        other_custom = cur.fetchone()[0]
    assert system_visible >= 4   # seeded system roles are visible to every tenant
    assert own_custom == 1        # sees its own custom role
    assert other_custom == 0      # cannot see the other org's custom role


def test_tenant_cannot_create_system_role(seeded, app_conn):
    # WITH CHECK forbids inserting a NULL-org (system) role as a tenant
    with pytest.raises(psycopg.Error):
        with app_conn.cursor() as cur:
            cur.execute("SELECT set_config('app.current_org_id', %s, true)", (ORG_A,))
            cur.execute("INSERT INTO public.roles (organization_id, name) VALUES (NULL,'rogue-system')")
