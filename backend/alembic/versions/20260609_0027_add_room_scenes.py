"""add room scenes

Revision ID: 20260609_0027
Revises: 20260609_0026
Create Date: 2026-06-09 00:27:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260609_0027"
down_revision: str | None = "20260609_0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_scenes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_scenes_id"), "room_scenes", ["id"], unique=False)
    op.create_index(op.f("ix_room_scenes_room_id"), "room_scenes", ["room_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_room_scenes_room_id"), table_name="room_scenes")
    op.drop_index(op.f("ix_room_scenes_id"), table_name="room_scenes")
    op.drop_table("room_scenes")
