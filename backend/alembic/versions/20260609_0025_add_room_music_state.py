"""add room music state

Revision ID: 20260609_0025
Revises: 20260609_0024
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "20260609_0025"
down_revision = "20260609_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("room_tabletop_settings", sa.Column("music_state", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("room_tabletop_settings", "music_state")
