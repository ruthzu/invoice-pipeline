"""Remove PROCESSED from invoice status enum.

Revision ID: 006
Revises: 005
Create Date: 2026-08-24 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_STATUSES_WITHOUT_PROCESSED = (
    "PENDING",
    "QUEUED",
    "EXTRACTED",
    "EXTRACTION_FAILED",
    "NEEDS_REVIEW",
    "AUTO_APPROVED",
    "APPROVED",
    "REJECTED",
)
_STATUSES_WITH_PROCESSED = (
    *_STATUSES_WITHOUT_PROCESSED[:2],
    "PROCESSED",
    *_STATUSES_WITHOUT_PROCESSED[2:],
)


def _enum_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM invoices WHERE status::text = 'PROCESSED') THEN
                RAISE EXCEPTION
                    'Cannot remove PROCESSED: invoices with PROCESSED status exist';
            END IF;
        END
        $$;
        """
    )
    op.execute(
        "CREATE TYPE invoicestatus_new AS ENUM "
        f"({_enum_values(_STATUSES_WITHOUT_PROCESSED)})"
    )
    op.execute(
        "ALTER TABLE invoices ALTER COLUMN status TYPE invoicestatus_new "
        "USING status::text::invoicestatus_new"
    )
    op.execute("DROP TYPE invoicestatus")
    op.execute("ALTER TYPE invoicestatus_new RENAME TO invoicestatus")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE invoicestatus_old AS ENUM "
        f"({_enum_values(_STATUSES_WITH_PROCESSED)})"
    )
    op.execute(
        "ALTER TABLE invoices ALTER COLUMN status TYPE invoicestatus_old "
        "USING status::text::invoicestatus_old"
    )
    op.execute("DROP TYPE invoicestatus")
    op.execute("ALTER TYPE invoicestatus_old RENAME TO invoicestatus")
