"""add warning number to geometries table

Revision ID: 44bbe95fe9a0
Revises: 117aba98fd74
Create Date: 2025-11-19 ...
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "44bbe95fe9a0"
down_revision: Union[str, Sequence[str], None] = "117aba98fd74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add warning_number column and populate from existing data."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        # Add column
        op.add_column(
            "warning_geometries",
            sa.Column("warning_number", sa.String(), nullable=True),
        )

        # Populate from warnings table
        conn.execute(
            sa.text("""
            UPDATE warning_geometries wg
            SET warning_number = w.warning_number
            FROM warnings w
            WHERE wg.warning_id = w.id
        """)
        )

        # Make not nullable after populating
        op.alter_column("warning_geometries", "warning_number", nullable=False)

        # Add index
        op.create_index(
            "idx_warning_number_day",
            "warning_geometries",
            ["warning_number", "day_number"],
        )

        print("✓ Added warning_number to warning_geometries")
    else:
        print("⊘ Skipping (SQLite)")


def downgrade() -> None:
    """Remove warning_number column."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        op.drop_index("idx_warning_number_day")
        op.drop_column("warning_geometries", "warning_number")
        print("✓ Removed warning_number")
    else:
        print("⊘ Skipping (SQLite)")
