"""Add extraction columns and invoicestatus enum values

Revision ID: 003
Revises: 002
Create Date: 2026-08-19 09:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'EXTRACTED'")
    op.execute(
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'EXTRACTION_FAILED'"
    )
    op.add_column(
        "invoices",
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("extraction_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invoices", "extraction_error")
    op.drop_column("invoices", "extracted_data")
    # PostgreSQL does not support removing individual enum values.
