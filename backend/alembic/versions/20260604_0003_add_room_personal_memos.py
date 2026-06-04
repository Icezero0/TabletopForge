"""add room_personal_memos

Revision ID: 20260604_0003
Revises: 20260604_0002
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0003"
down_revision: str | None = "20260604_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_personal_memos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "room_id", name="uq_room_personal_memos_user_room"),
    )
    op.create_index(op.f("ix_room_personal_memos_id"), "room_personal_memos", ["id"], unique=False)
    op.create_index(op.f("ix_room_personal_memos_room_id"), "room_personal_memos", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_personal_memos_user_id"), "room_personal_memos", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_room_personal_memos_user_id"), table_name="room_personal_memos")
    op.drop_index(op.f("ix_room_personal_memos_room_id"), table_name="room_personal_memos")
    op.drop_index(op.f("ix_room_personal_memos_id"), table_name="room_personal_memos")
    op.drop_table("room_personal_memos")
