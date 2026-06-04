"""add room_members.game_role

Revision ID: 20260604_0002
Revises: 20260604_0001
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0002"
down_revision: str | None = "20260604_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "room_members",
        sa.Column(
            "game_role",
            sa.String(length=8),
            server_default="PL",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("room_members", "game_role")
