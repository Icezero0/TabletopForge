"""add room combat state

Revision ID: 20260609_0024
Revises: 20260609_0023
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "20260609_0024"
down_revision = "20260609_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("room_tabletop_settings", sa.Column("combat_state", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("room_tabletop_settings", "combat_state")
