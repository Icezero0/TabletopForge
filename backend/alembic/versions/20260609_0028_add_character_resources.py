"""add character resources

Revision ID: 20260609_0028
Revises: 20260609_0027
Create Date: 2026-06-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20260609_0028"
down_revision = "20260609_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("resources", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("characters", "resources")
