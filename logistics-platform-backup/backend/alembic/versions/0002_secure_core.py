"""Secure-core schema: organizations, users, memberships, RBAC, audit.

Revision: 0002_secure_core
Down:     0001_foundation

Conventions (per docs/CONVENTIONS.md): snake_case plural tables; PK `id`; FKs `<entity>_id`;
unique `uq_*`; index `ix_*`; check `ck_*`. Every table carries the standard envelope
(UUIDv7 id, created_at, updated_at, created_by, updated_by, deleted_at, version) EXCEPT
`audit_logs`, which is append-only and therefore immutable (no updated_*/deleted_at/version).

Tenancy:
  * `users` is GLOBAL — no organization_id, no RLS (identity is shared across orgs).
  * `permissions` is a GLOBAL catalog — no organization_id, no RLS (static platform data).
  * `roles` / `role_permissions` are HYBRID — organization_id NULL ⇒ system (shared, seeded),
    non-NULL ⇒ org-custom. RLS isolates custom rows; a permissive SELECT policy exposes system rows.
  * organizations, user_organizations, user_organization_roles, audit_logs are org-scoped:
    `app.enable_org_rls()` is called on each IN THIS MIGRATION.
  * `organizations` carries a generated `organization_id = id` so the uniform org-isolation policy
    applies to the tenant root too (an org sees only itself).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_secure_core"
down_revision: Union[str, None] = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ tables
    op.execute(
        """
        -- users: GLOBAL identity (no organization_id)
        CREATE TABLE public.users (
            id            uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            email         text NOT NULL,
            password_hash text,
            full_name     text,
            status        text NOT NULL DEFAULT 'active',
            email_verified_at timestamptz,
            created_at    timestamptz NOT NULL DEFAULT now(),
            updated_at    timestamptz NOT NULL DEFAULT now(),
            created_by    uuid REFERENCES public.users(id),
            updated_by    uuid REFERENCES public.users(id),
            deleted_at    timestamptz,
            version       integer NOT NULL DEFAULT 1,
            CONSTRAINT ck_users_status CHECK (status IN ('active','invited','suspended','disabled'))
        );

        -- organizations: tenant root; generated organization_id = id for uniform RLS
        CREATE TABLE public.organizations (
            id              uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            organization_id uuid GENERATED ALWAYS AS (id) STORED,
            name            text NOT NULL,
            slug            text NOT NULL,
            gstin           text,
            country_code    char(2) NOT NULL DEFAULT 'IN',
            currency        char(3) NOT NULL DEFAULT 'INR',
            status          text NOT NULL DEFAULT 'active',
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now(),
            created_by      uuid REFERENCES public.users(id),
            updated_by      uuid REFERENCES public.users(id),
            deleted_at      timestamptz,
            version         integer NOT NULL DEFAULT 1,
            CONSTRAINT ck_organizations_status CHECK (status IN ('active','suspended','closed'))
        );

        -- user_organizations: membership = the tenant boundary
        CREATE TABLE public.user_organizations (
            id              uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            user_id         uuid NOT NULL REFERENCES public.users(id),
            organization_id uuid NOT NULL REFERENCES public.organizations(id),
            status          text NOT NULL DEFAULT 'active',
            is_primary      boolean NOT NULL DEFAULT false,
            invited_by      uuid REFERENCES public.users(id),
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now(),
            created_by      uuid REFERENCES public.users(id),
            updated_by      uuid REFERENCES public.users(id),
            deleted_at      timestamptz,
            version         integer NOT NULL DEFAULT 1,
            CONSTRAINT ck_user_organizations_status
                CHECK (status IN ('active','invited','suspended','removed'))
        );

        -- permissions: GLOBAL catalog
        CREATE TABLE public.permissions (
            id          uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            key         text NOT NULL,
            description text,
            created_at  timestamptz NOT NULL DEFAULT now(),
            updated_at  timestamptz NOT NULL DEFAULT now(),
            created_by  uuid REFERENCES public.users(id),
            updated_by  uuid REFERENCES public.users(id),
            deleted_at  timestamptz,
            version     integer NOT NULL DEFAULT 1
        );

        -- roles: HYBRID (organization_id NULL ⇒ system, else org-custom)
        CREATE TABLE public.roles (
            id              uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            organization_id uuid REFERENCES public.organizations(id),
            name            text NOT NULL,
            description     text,
            is_system       boolean NOT NULL DEFAULT false,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now(),
            created_by      uuid REFERENCES public.users(id),
            updated_by      uuid REFERENCES public.users(id),
            deleted_at      timestamptz,
            version         integer NOT NULL DEFAULT 1
        );

        -- role_permissions: maps role → permission (organization_id mirrors role scope)
        CREATE TABLE public.role_permissions (
            id              uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            role_id         uuid NOT NULL REFERENCES public.roles(id) ON DELETE CASCADE,
            permission_id   uuid NOT NULL REFERENCES public.permissions(id),
            organization_id uuid REFERENCES public.organizations(id),
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now(),
            created_by      uuid REFERENCES public.users(id),
            updated_by      uuid REFERENCES public.users(id),
            deleted_at      timestamptz,
            version         integer NOT NULL DEFAULT 1
        );

        -- user_organization_roles: assigns a role within a membership (org-scoped)
        CREATE TABLE public.user_organization_roles (
            id                   uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            user_organization_id uuid NOT NULL REFERENCES public.user_organizations(id) ON DELETE CASCADE,
            role_id              uuid NOT NULL REFERENCES public.roles(id),
            organization_id      uuid NOT NULL REFERENCES public.organizations(id),
            created_at           timestamptz NOT NULL DEFAULT now(),
            updated_at           timestamptz NOT NULL DEFAULT now(),
            created_by           uuid REFERENCES public.users(id),
            updated_by           uuid REFERENCES public.users(id),
            deleted_at           timestamptz,
            version              integer NOT NULL DEFAULT 1
        );

        -- audit_logs: append-only / immutable (no updated_*/deleted_at/version)
        CREATE TABLE public.audit_logs (
            id              uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            organization_id uuid REFERENCES public.organizations(id),
            actor_user_id   uuid REFERENCES public.users(id),
            action          text NOT NULL,
            entity_type     text,
            entity_id       uuid,
            metadata        jsonb NOT NULL DEFAULT '{}'::jsonb,
            ip_address      inet,
            user_agent      text,
            created_at      timestamptz NOT NULL DEFAULT now()
        );
        """
    )

    # ----------------------------------------------------------------- indexes
    op.execute(
        """
        CREATE UNIQUE INDEX uq_users_email ON public.users (lower(email)) WHERE deleted_at IS NULL;
        CREATE INDEX ix_users_status ON public.users (status) WHERE deleted_at IS NULL;

        CREATE UNIQUE INDEX uq_organizations_slug ON public.organizations (lower(slug)) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX uq_organizations_gstin ON public.organizations (gstin)
            WHERE gstin IS NOT NULL AND deleted_at IS NULL;

        CREATE UNIQUE INDEX uq_user_organizations_membership
            ON public.user_organizations (user_id, organization_id) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX uq_user_organizations_primary
            ON public.user_organizations (user_id) WHERE is_primary AND deleted_at IS NULL;
        CREATE INDEX ix_user_organizations_org ON public.user_organizations (organization_id);
        CREATE INDEX ix_user_organizations_user ON public.user_organizations (user_id);

        CREATE UNIQUE INDEX uq_permissions_key ON public.permissions (key) WHERE deleted_at IS NULL;

        CREATE UNIQUE INDEX uq_roles_system_name ON public.roles (lower(name))
            WHERE organization_id IS NULL AND deleted_at IS NULL;
        CREATE UNIQUE INDEX uq_roles_org_name ON public.roles (organization_id, lower(name))
            WHERE organization_id IS NOT NULL AND deleted_at IS NULL;
        CREATE INDEX ix_roles_org ON public.roles (organization_id);

        CREATE UNIQUE INDEX uq_role_permissions ON public.role_permissions (role_id, permission_id)
            WHERE deleted_at IS NULL;
        CREATE INDEX ix_role_permissions_org ON public.role_permissions (organization_id);

        CREATE UNIQUE INDEX uq_user_organization_roles
            ON public.user_organization_roles (user_organization_id, role_id) WHERE deleted_at IS NULL;
        CREATE INDEX ix_user_organization_roles_org ON public.user_organization_roles (organization_id);

        CREATE INDEX ix_audit_logs_org_created ON public.audit_logs (organization_id, created_at DESC);
        CREATE INDEX ix_audit_logs_actor ON public.audit_logs (actor_user_id);
        CREATE INDEX ix_audit_logs_entity ON public.audit_logs (entity_type, entity_id);
        CREATE INDEX ix_audit_logs_action ON public.audit_logs (action);
        """
    )

    # ---------------------------------------------------------------- triggers
    op.execute(
        """
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.users
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.organizations
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.user_organizations
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.permissions
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.roles
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.role_permissions
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.user_organization_roles
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();

        -- append-only enforcement for audit_logs (defence in depth alongside grant restrictions)
        CREATE OR REPLACE FUNCTION app.deny_mutation() RETURNS trigger
            LANGUAGE plpgsql AS $deny$
        BEGIN
            RAISE EXCEPTION 'append-only table: % operations are not permitted', TG_OP;
        END;
        $deny$;
        CREATE TRIGGER audit_logs_immutable BEFORE UPDATE OR DELETE ON public.audit_logs
            FOR EACH ROW EXECUTE FUNCTION app.deny_mutation();
        """
    )

    # --------------------------------------------------------------------- RLS
    op.execute(
        """
        SELECT app.enable_org_rls('public.organizations');
        SELECT app.enable_org_rls('public.user_organizations');
        SELECT app.enable_org_rls('public.user_organization_roles');
        SELECT app.enable_org_rls('public.audit_logs');

        -- hybrid: org-isolation + permissive read of shared system rows (organization_id IS NULL)
        SELECT app.enable_org_rls('public.roles');
        CREATE POLICY system_roles_readable ON public.roles FOR SELECT USING (organization_id IS NULL);

        SELECT app.enable_org_rls('public.role_permissions');
        CREATE POLICY system_role_permissions_readable ON public.role_permissions
            FOR SELECT USING (organization_id IS NULL);
        """
    )

    # ------------------------------------------------------------------ grants
    op.execute(
        """
        DO $grants$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                GRANT SELECT, UPDATE ON public.organizations TO app_user;          -- soft-delete via UPDATE
                GRANT SELECT, UPDATE ON public.users TO app_user;                  -- insert via privileged registration
                GRANT SELECT, INSERT, UPDATE ON public.user_organizations TO app_user;
                GRANT SELECT ON public.permissions TO app_user;                    -- read-only catalog
                GRANT SELECT, INSERT, UPDATE, DELETE ON public.roles TO app_user;
                GRANT SELECT, INSERT, UPDATE, DELETE ON public.role_permissions TO app_user;
                GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_organization_roles TO app_user;
                GRANT SELECT, INSERT ON public.audit_logs TO app_user;             -- append-only
            END IF;
        END
        $grants$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS public.audit_logs CASCADE;
        DROP TABLE IF EXISTS public.user_organization_roles CASCADE;
        DROP TABLE IF EXISTS public.role_permissions CASCADE;
        DROP TABLE IF EXISTS public.roles CASCADE;
        DROP TABLE IF EXISTS public.permissions CASCADE;
        DROP TABLE IF EXISTS public.user_organizations CASCADE;
        DROP TABLE IF EXISTS public.organizations CASCADE;
        DROP TABLE IF EXISTS public.users CASCADE;
        DROP FUNCTION IF EXISTS app.deny_mutation();
        """
    )
