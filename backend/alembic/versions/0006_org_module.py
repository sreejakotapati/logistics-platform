"""Users & Organizations module: org profile/settings columns + invitations.

Revision: 0006_org_module
Down:     0005_tenancy

Adds organization profile fields and a JSONB `settings` bag to `organizations`, and a new org-scoped
`org_invitations` table (RLS-enforced like every tenant table). Invitations are tenant data; accepting
one is an identity-plane action (the invitee is not yet a member), handled by the service on the
privileged session.
"""
from typing import Union

from alembic import op

revision: str = "0006_org_module"
down_revision: Union[str, None] = "0005_tenancy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- organization profile + settings -----------------------------------
    op.execute(
        """
        ALTER TABLE public.organizations
            ADD COLUMN legal_name     text,
            ADD COLUMN contact_email  text,
            ADD COLUMN contact_phone  text,
            ADD COLUMN website        text,
            ADD COLUMN address_line1  text,
            ADD COLUMN address_line2  text,
            ADD COLUMN city           text,
            ADD COLUMN state          text,
            ADD COLUMN postal_code    text,
            ADD COLUMN settings       jsonb NOT NULL DEFAULT '{}'::jsonb;
        """
    )

    # ---- org_invitations (org-scoped, RLS) ---------------------------------
    op.execute(
        """
        CREATE TABLE public.org_invitations (
            id               uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            organization_id  uuid NOT NULL REFERENCES public.organizations(id),
            email            text NOT NULL,
            role_id          uuid REFERENCES public.roles(id),
            invited_by       uuid REFERENCES public.users(id),
            token_hash       text NOT NULL,
            status           text NOT NULL DEFAULT 'pending',
            expires_at       timestamptz NOT NULL,
            accepted_at      timestamptz,
            accepted_user_id uuid REFERENCES public.users(id),
            created_at       timestamptz NOT NULL DEFAULT now(),
            updated_at       timestamptz NOT NULL DEFAULT now(),
            created_by       uuid REFERENCES public.users(id),
            updated_by       uuid REFERENCES public.users(id),
            deleted_at       timestamptz,
            version          integer NOT NULL DEFAULT 1,
            CONSTRAINT ck_org_invitations_status
                CHECK (status IN ('pending','accepted','revoked','expired'))
        );
        CREATE UNIQUE INDEX uq_org_invitations_token_hash ON public.org_invitations (token_hash);
        CREATE UNIQUE INDEX uq_org_invitations_pending_email
            ON public.org_invitations (organization_id, lower(email))
            WHERE status = 'pending' AND deleted_at IS NULL;
        CREATE INDEX ix_org_invitations_org ON public.org_invitations (organization_id);
        CREATE INDEX ix_org_invitations_email ON public.org_invitations (lower(email));

        CREATE TRIGGER set_updated_at BEFORE UPDATE ON public.org_invitations
            FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();

        SELECT app.enable_org_rls('public.org_invitations');
        """
    )

    # ---- grants ------------------------------------------------------------
    op.execute(
        """
        DO $grants$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                GRANT SELECT, INSERT, UPDATE ON public.org_invitations TO app_user;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_superadmin') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON public.org_invitations TO app_superadmin;
            END IF;
        END
        $grants$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.org_invitations CASCADE;")
    op.execute(
        """
        ALTER TABLE public.organizations
            DROP COLUMN IF EXISTS legal_name, DROP COLUMN IF EXISTS contact_email,
            DROP COLUMN IF EXISTS contact_phone, DROP COLUMN IF EXISTS website,
            DROP COLUMN IF EXISTS address_line1, DROP COLUMN IF EXISTS address_line2,
            DROP COLUMN IF EXISTS city, DROP COLUMN IF EXISTS state,
            DROP COLUMN IF EXISTS postal_code, DROP COLUMN IF EXISTS settings;
        """
    )
