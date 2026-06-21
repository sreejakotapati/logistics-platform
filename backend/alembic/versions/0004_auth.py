"""Auth/identity-plane tables: refresh-token rotation records and single-use tokens.

Revision: 0004_auth
Down:     0003_seed_rbac

These are IDENTITY-plane tables (like `users`): no organization_id and no org RLS, because auth
happens before/around any org context. They store only HASHES of tokens, never the tokens themselves,
and are never exposed through the API. Access is via the privileged identity session.
"""
from typing import Union

from alembic import op

revision: str = "0004_auth"
down_revision: Union[str, None] = "0003_seed_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- Rotating refresh tokens. One "family" per login; rotation chains via replaced_by.
        CREATE TABLE public.auth_refresh_tokens (
            id             uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            user_id        uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            family_id      uuid NOT NULL,
            token_hash     text NOT NULL,
            issued_at      timestamptz NOT NULL DEFAULT now(),
            expires_at     timestamptz NOT NULL,
            rotated_at     timestamptz,
            revoked_at     timestamptz,
            revoked_reason text,
            replaced_by    uuid REFERENCES public.auth_refresh_tokens(id),
            ip_address     inet,
            user_agent     text
        );
        CREATE UNIQUE INDEX uq_auth_refresh_tokens_token_hash ON public.auth_refresh_tokens (token_hash);
        CREATE INDEX ix_auth_refresh_tokens_user ON public.auth_refresh_tokens (user_id);
        CREATE INDEX ix_auth_refresh_tokens_family ON public.auth_refresh_tokens (family_id);
        CREATE INDEX ix_auth_refresh_tokens_expires ON public.auth_refresh_tokens (expires_at);

        -- Single-use tokens for email verification and password reset.
        CREATE TABLE public.auth_tokens (
            id          uuid PRIMARY KEY DEFAULT app.uuid_generate_v7(),
            user_id     uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            purpose     text NOT NULL,
            token_hash  text NOT NULL,
            expires_at  timestamptz NOT NULL,
            consumed_at timestamptz,
            created_at  timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_auth_tokens_purpose CHECK (purpose IN ('email_verification','password_reset'))
        );
        CREATE UNIQUE INDEX uq_auth_tokens_token_hash ON public.auth_tokens (token_hash);
        CREATE INDEX ix_auth_tokens_user_purpose ON public.auth_tokens (user_id, purpose);
        """
    )

    # Grants. Identity-plane tables are used by the privileged session; grant both auth roles if present.
    op.execute(
        """
        DO $grants$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_superadmin') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON public.auth_refresh_tokens TO app_superadmin;
                GRANT SELECT, INSERT, UPDATE, DELETE ON public.auth_tokens TO app_superadmin;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                GRANT SELECT, INSERT, UPDATE ON public.auth_refresh_tokens TO app_user;
                GRANT SELECT, INSERT, UPDATE ON public.auth_tokens TO app_user;
            END IF;
        END
        $grants$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS public.auth_tokens CASCADE;
        DROP TABLE IF EXISTS public.auth_refresh_tokens CASCADE;
        """
    )
