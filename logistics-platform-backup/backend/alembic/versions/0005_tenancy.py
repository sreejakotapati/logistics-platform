"""Carry the active organization on the refresh session (org-switch continuity).

Revision: 0005_tenancy
Down:     0004_auth

Without this, a refresh would always snap the active org back to the user's primary. Storing the active
org on the refresh record lets org-switch persist across refreshes: switch updates this column, and
rotation carries it forward.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005_tenancy"
down_revision: Union[str, None] = "0004_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE public.auth_refresh_tokens
            ADD COLUMN active_organization_id uuid REFERENCES public.organizations(id);
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE public.auth_refresh_tokens DROP COLUMN IF EXISTS active_organization_id;"
    )
