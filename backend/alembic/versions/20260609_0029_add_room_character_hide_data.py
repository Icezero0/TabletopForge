"""add room character hide data

Revision ID: 20260609_0029
Revises: 20260609_0028
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260609_0029"
down_revision = "20260609_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "room_characters",
        sa.Column("hide_data", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("room_characters", "hide_data")
