"""add room fog state

Revision ID: 20260609_0026
Revises: 20260609_0025
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260609_0026"
down_revision = "20260609_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("room_tabletop_settings", sa.Column("fog_state", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("room_tabletop_settings", "fog_state")
