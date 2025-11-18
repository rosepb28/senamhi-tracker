"""add geospatial point column to locations

Revision ID: 6e7f3b38a2a2
Revises: 64779774da5c
Create Date: 2025-11-18 XX:XX:XX.XXXXXX

"""

from alembic import op
import sqlalchemy as sa

# Import geoalchemy2 only if available
try:
    from geoalchemy2 import Geometry

    GEOALCHEMY2_AVAILABLE = True
except ImportError:
    GEOALCHEMY2_AVAILABLE = False

# revision identifiers, used by Alembic.
revision = "6e7f3b38a2a2"
down_revision = "64779774da5c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add geospatial point column (PostgreSQL + PostGIS only)."""
    conn = op.get_bind()

    # Check if we're on PostgreSQL
    if conn.dialect.name == "postgresql" and GEOALCHEMY2_AVAILABLE:
        # Enable PostGIS extension
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

        # Add geometry column
        op.add_column(
            "locations", sa.Column("point", Geometry("POINT", srid=4326), nullable=True)
        )

        # Create spatial index
        op.create_index(
            "idx_location_point",
            "locations",
            ["point"],
            unique=False,
            postgresql_using="gist",
        )

        print("✓ Added PostGIS point column and spatial index")
    else:
        # SQLite or PostGIS not available - skip migration
        print("⊘ Skipping PostGIS column (using SQLite or PostGIS unavailable)")


def downgrade() -> None:
    """Remove geospatial point column."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        op.drop_index("idx_location_point", table_name="locations")
        op.drop_column("locations", "point")
        print("✓ Removed PostGIS point column")
    else:
        print("⊘ Nothing to downgrade (SQLite)")
