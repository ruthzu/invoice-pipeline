"""Add review routing statuses and fields

Revision ID: 005
Revises: 004
Create Date: 2026-08-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for status in ("NEEDS_REVIEW", "AUTO_APPROVED", "APPROVED", "REJECTED"):
        op.execute(f"ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS '{status}'")

    op.add_column("invoices", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("reviewed_by", sa.Text(), nullable=True))
    op.add_column(
        "invoices",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invoices", "reviewed_at")
    op.drop_column("invoices", "reviewed_by")
    op.drop_column("invoices", "rejection_reason")
    # PostgreSQL does not support removing individual enum values.
