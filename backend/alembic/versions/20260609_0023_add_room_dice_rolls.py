"""add room dice rolls

Revision ID: 20260609_0023
Revises: 20260609_0022
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "20260609_0023"
down_revision = "20260609_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "room_dice_rolls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("roller_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("actor_token_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=255), server_default="", nullable=False),
        sa.Column("formula", sa.String(length=255), nullable=False),
        sa.Column("visibility", sa.String(length=16), server_default="public", nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["actor_token_id"], ["room_tokens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["roller_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_dice_rolls_id"), "room_dice_rolls", ["id"], unique=False)
    op.create_index(op.f("ix_room_dice_rolls_room_id"), "room_dice_rolls", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_dice_rolls_roller_user_id"), "room_dice_rolls", ["roller_user_id"], unique=False)
    op.create_index(op.f("ix_room_dice_rolls_actor_token_id"), "room_dice_rolls", ["actor_token_id"], unique=False)
    op.create_index(op.f("ix_room_dice_rolls_created_at"), "room_dice_rolls", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_room_dice_rolls_created_at"), table_name="room_dice_rolls")
    op.drop_index(op.f("ix_room_dice_rolls_actor_token_id"), table_name="room_dice_rolls")
    op.drop_index(op.f("ix_room_dice_rolls_roller_user_id"), table_name="room_dice_rolls")
    op.drop_index(op.f("ix_room_dice_rolls_room_id"), table_name="room_dice_rolls")
    op.drop_index(op.f("ix_room_dice_rolls_id"), table_name="room_dice_rolls")
    op.drop_table("room_dice_rolls")
