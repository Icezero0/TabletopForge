"""add room_members.player_color

Revision ID: 20260606_0011
Revises: 20260606_0010
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0011"
down_revision: str | None = "20260606_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "room_members",
        sa.Column("player_color", sa.String(length=7), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("room_members", "player_color")
