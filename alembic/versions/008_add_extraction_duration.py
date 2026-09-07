"""Add extraction duration to invoices.

Revision ID: 008
Revises: 007
Create Date: 2026-09-06 20:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "invoices", sa.Column("extraction_duration_ms", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("invoices", "extraction_duration_ms")
