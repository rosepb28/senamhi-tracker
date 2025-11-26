"""add warning daily details table

Revision ID: f8c1e4e56594
Revises: 44bbe95fe9a0
Create Date: 2025-11-22 12:08:38.114095
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "f8c1e4e56594"
down_revision = "44bbe95fe9a0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "warning_daily_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("warning_number", sa.String(50), nullable=False),  # SIN ForeignKey
        sa.Column("senamhi_id", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("nivel", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("affected_provinces", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "warning_number", "department", "day_number", name="uq_warning_dept_day"
        ),
    )

    op.create_index(
        "ix_warning_daily_details_warning", "warning_daily_details", ["warning_number"]
    )

    op.create_index(
        "ix_warning_daily_details_dept", "warning_daily_details", ["department"]
    )

    print("✓ Created warning_daily_details table")


def downgrade():
    op.drop_index("ix_warning_daily_details_dept", table_name="warning_daily_details")
    op.drop_index(
        "ix_warning_daily_details_warning", table_name="warning_daily_details"
    )
    op.drop_table("warning_daily_details")

    print("✓ Dropped warning_daily_details table")
