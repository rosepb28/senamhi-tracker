"""add senamhi_id to warnings

Revision ID: e6405562e4b0
Revises: 6e7f3b38a2a2
Create Date: 2025-11-18 16:47:39.190741

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6405562e4b0"
down_revision: Union[str, Sequence[str], None] = "6e7f3b38a2a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add column as nullable first (for existing data)
    op.add_column("warnings", sa.Column("senamhi_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_warnings_senamhi_id"), "warnings", ["senamhi_id"], unique=False
    )

    # Note: Future scrapes will populate senamhi_id
    # Existing warnings without senamhi_id will need to be re-scraped or manually updated


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_warnings_senamhi_id"), table_name="warnings")
    op.drop_column("warnings", "senamhi_id")
