"""Idempotent seed: permission catalog, system roles, system role→permission mappings.

Revision: 0003_seed_rbac
Down:     0002_secure_core

Idempotent by construction (INSERT ... WHERE NOT EXISTS on natural keys), so it is safe to re-run.
System rows live with organization_id IS NULL. Because `roles` / `role_permissions` are RLS-FORCEd,
RLS is briefly toggled off around the system-row inserts (the migration runs single-threaded as the
table owner). `permissions` is a global table (no RLS) and is seeded directly.
"""
from typing import Union

from alembic import op

revision: str = "0003_seed_rbac"
down_revision: Union[str, None] = "0002_secure_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- permission catalog (global table, no RLS) -------------------------
    op.execute(
        """
        INSERT INTO public.permissions (key, description)
        SELECT v.key, v.description
        FROM (VALUES
            ('org:read',       'View organization profile'),
            ('org:update',     'Update organization profile'),
            ('org:provision',  'Provision a new organization (platform)'),
            ('org:suspend',    'Suspend or close an organization (platform)'),
            ('users:read',     'View members of the organization'),
            ('users:invite',   'Invite a user to the organization'),
            ('users:update',   'Update a member or membership'),
            ('users:remove',   'Remove a member from the organization'),
            ('roles:read',     'View roles and permissions'),
            ('roles:manage',   'Create or modify roles and assignments'),
            ('audit:read',     'View the audit log')
        ) AS v(key, description)
        WHERE NOT EXISTS (SELECT 1 FROM public.permissions p WHERE p.key = v.key);
        """
    )

    # ---- system roles (organization_id IS NULL) ----------------------------
    op.execute(
        """
        ALTER TABLE public.roles DISABLE ROW LEVEL SECURITY;
        INSERT INTO public.roles (organization_id, name, description, is_system)
        SELECT NULL, v.name, v.description, true
        FROM (VALUES
            ('Super Admin', 'Platform-wide administrator'),
            ('Org Admin',   'Organization administrator'),
            ('Manager',     'Manages operations within the organization'),
            ('Member',      'Standard organization member')
        ) AS v(name, description)
        WHERE NOT EXISTS (
            SELECT 1 FROM public.roles r
            WHERE r.organization_id IS NULL AND lower(r.name) = lower(v.name)
        );
        ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.roles FORCE ROW LEVEL SECURITY;
        """
    )

    # ---- system role → permission mappings ---------------------------------
    op.execute(
        """
        ALTER TABLE public.role_permissions DISABLE ROW LEVEL SECURITY;

        -- Super Admin: every permission
        INSERT INTO public.role_permissions (role_id, permission_id, organization_id)
        SELECT r.id, p.id, NULL
        FROM public.roles r CROSS JOIN public.permissions p
        WHERE r.organization_id IS NULL AND lower(r.name) = 'super admin'
          AND NOT EXISTS (SELECT 1 FROM public.role_permissions rp
                          WHERE rp.role_id = r.id AND rp.permission_id = p.id);

        -- Org Admin
        INSERT INTO public.role_permissions (role_id, permission_id, organization_id)
        SELECT r.id, p.id, NULL
        FROM public.roles r JOIN public.permissions p
          ON p.key IN ('org:read','org:update','users:read','users:invite','users:update',
                       'users:remove','roles:read','roles:manage','audit:read')
        WHERE r.organization_id IS NULL AND lower(r.name) = 'org admin'
          AND NOT EXISTS (SELECT 1 FROM public.role_permissions rp
                          WHERE rp.role_id = r.id AND rp.permission_id = p.id);

        -- Manager
        INSERT INTO public.role_permissions (role_id, permission_id, organization_id)
        SELECT r.id, p.id, NULL
        FROM public.roles r JOIN public.permissions p
          ON p.key IN ('org:read','users:read','users:invite','users:update','roles:read')
        WHERE r.organization_id IS NULL AND lower(r.name) = 'manager'
          AND NOT EXISTS (SELECT 1 FROM public.role_permissions rp
                          WHERE rp.role_id = r.id AND rp.permission_id = p.id);

        -- Member
        INSERT INTO public.role_permissions (role_id, permission_id, organization_id)
        SELECT r.id, p.id, NULL
        FROM public.roles r JOIN public.permissions p
          ON p.key IN ('org:read','users:read','roles:read')
        WHERE r.organization_id IS NULL AND lower(r.name) = 'member'
          AND NOT EXISTS (SELECT 1 FROM public.role_permissions rp
                          WHERE rp.role_id = r.id AND rp.permission_id = p.id);

        ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.role_permissions FORCE ROW LEVEL SECURITY;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE public.role_permissions DISABLE ROW LEVEL SECURITY;
        DELETE FROM public.role_permissions WHERE organization_id IS NULL;
        ALTER TABLE public.role_permissions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.role_permissions FORCE ROW LEVEL SECURITY;

        ALTER TABLE public.roles DISABLE ROW LEVEL SECURITY;
        DELETE FROM public.roles WHERE organization_id IS NULL AND is_system;
        ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
        ALTER TABLE public.roles FORCE ROW LEVEL SECURITY;

        DELETE FROM public.permissions
        WHERE key IN ('org:read','org:update','org:provision','org:suspend','users:read',
                      'users:invite','users:update','users:remove','roles:read','roles:manage','audit:read');
        """
    )
