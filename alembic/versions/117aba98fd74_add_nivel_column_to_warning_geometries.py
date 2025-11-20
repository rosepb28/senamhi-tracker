"""add nivel column to warning geometries

Revision ID: 117aba98fd74
Revises: 74434f1812a6
Create Date: 2025-11-19 ...
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "117aba98fd74"
down_revision: Union[str, Sequence[str], None] = "74434f1812a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nivel column to warning_geometries table."""
    conn = op.get_bind()

    # Only add column on PostgreSQL
    if conn.dialect.name == "postgresql":
        op.add_column(
            "warning_geometries", sa.Column("nivel", sa.Integer(), nullable=True)
        )
        print("✓ Added nivel column to warning_geometries")
    else:
        print("⊘ Skipping (SQLite)")


def downgrade() -> None:
    """Remove nivel column."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        op.drop_column("warning_geometries", "nivel")
        print("✓ Removed nivel column")
    else:
        print("⊘ Skipping (SQLite)")
