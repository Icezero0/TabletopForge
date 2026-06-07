"""add is_hidden to room_characters

Revision ID: 20260607_0015
Revises: 20260607_0014
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "20260607_0015"
down_revision = "20260607_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "room_characters",
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("room_characters", "is_hidden")
