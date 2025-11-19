"""add warning_geometries table

Revision ID: 74434f1812a6
Revises: e6405562e4b0
Create Date: 2025-11-18 19:36:52.095092

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Import geoalchemy2 only if available
try:
    from geoalchemy2 import Geometry

    GEOALCHEMY2_AVAILABLE = True
except ImportError:
    GEOALCHEMY2_AVAILABLE = False

# revision identifiers, used by Alembic.
revision: str = "74434f1812a6"
down_revision: Union[str, Sequence[str], None] = "e6405562e4b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add warning_geometries table (PostgreSQL + PostGIS only)."""
    conn = op.get_bind()

    # Only create table on PostgreSQL
    if conn.dialect.name == "postgresql" and GEOALCHEMY2_AVAILABLE:
        # Create warning_geometries table
        op.create_table(
            "warning_geometries",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("warning_id", sa.Integer(), nullable=False),
            sa.Column("day_number", sa.Integer(), nullable=False),
            sa.Column("shapefile_url", sa.Text(), nullable=True),
            sa.Column("shapefile_path", sa.String(), nullable=True),
            sa.Column("downloaded_at", sa.DateTime(), nullable=True),
            sa.Column("geometry", Geometry("MULTIPOLYGON", srid=4326), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["warning_id"],
                ["warnings.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

        # Create indexes
        op.create_index(
            "ix_warning_geometries_id", "warning_geometries", ["id"], unique=False
        )
        op.create_index(
            "ix_warning_geometries_warning_id",
            "warning_geometries",
            ["warning_id"],
            unique=False,
        )
        op.create_index(
            "idx_warning_day",
            "warning_geometries",
            ["warning_id", "day_number"],
            unique=False,
        )
        op.create_index(
            "idx_warning_geometry",
            "warning_geometries",
            ["geometry"],
            unique=False,
            postgresql_using="gist",
        )

        print("✓ Created warning_geometries table with PostGIS support")
    else:
        print(
            "⊘ Skipping warning_geometries table (using SQLite or PostGIS unavailable)"
        )


def downgrade() -> None:
    """Remove warning_geometries table."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        op.drop_index("idx_warning_geometry", table_name="warning_geometries")
        op.drop_index("idx_warning_day", table_name="warning_geometries")
        op.drop_index(
            "ix_warning_geometries_warning_id", table_name="warning_geometries"
        )
        op.drop_index("ix_warning_geometries_id", table_name="warning_geometries")
        op.drop_table("warning_geometries")
        print("✓ Removed warning_geometries table")
    else:
        print("⊘ Nothing to downgrade (SQLite)")
