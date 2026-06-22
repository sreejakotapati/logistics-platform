"""Platform (Super Admin) registry for permission-based authorization.

Revision: 0007_rbac
Down:     0006_org_module

A platform admin resolves to the FULL permission catalog (so Super Admin authorization is permission-
based, never a role-name check). This is a global identity table (no org_id, no RLS) — being a platform
admin is cross-org by definition. It replaces the provisioning key: provisioning now requires the
`org:provision` permission, which only platform admins hold.
"""
from typing import Union

from alembic import op

revision: str = "0007_rbac"
down_revision: Union[str, None] = "0006_org_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE public.platform_admins (
            id         uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            user_id    uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            granted_by uuid REFERENCES public.users(id),
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE UNIQUE INDEX uq_platform_admins_user ON public.platform_admins (user_id);
        """
    )
    op.execute(
        """
        DO $grants$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_superadmin') THEN
                GRANT SELECT, INSERT, DELETE ON public.platform_admins TO app_superadmin;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                GRANT SELECT ON public.platform_admins TO app_user;
            END IF;
        END
        $grants$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.platform_admins CASCADE;")
