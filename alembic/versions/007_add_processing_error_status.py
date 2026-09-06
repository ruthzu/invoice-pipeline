"""Add PROCESSING_ERROR invoice status.

Revision ID: 007
Revises: 006
Create Date: 2026-09-02 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'PROCESSING_ERROR'")


def downgrade() -> None:
    # PostgreSQL does not support removing individual enum values.
    pass
