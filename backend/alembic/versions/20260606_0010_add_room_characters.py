"""add room_characters table

Revision ID: 20260606_0010
Revises: 20260606_0009
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0010"
down_revision: str | None = "20260606_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_characters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("added_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["added_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_characters_id"), "room_characters", ["id"], unique=False)
    op.create_index(
        op.f("ix_room_characters_room_id"),
        "room_characters",
        ["room_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_characters_character_id"),
        "room_characters",
        ["character_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_room_characters_character_id"), table_name="room_characters")
    op.drop_index(op.f("ix_room_characters_room_id"), table_name="room_characters")
    op.drop_index(op.f("ix_room_characters_id"), table_name="room_characters")
    op.drop_table("room_characters")
