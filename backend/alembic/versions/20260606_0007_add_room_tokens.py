"""add room_tokens table

Revision ID: 20260606_0007
Revises: 20260606_0006
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0007"
down_revision: str | None = "20260606_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("linked_character_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("token_type", sa.String(length=16), server_default="character", nullable=False),
        sa.Column("x", sa.Float(), server_default="0", nullable=False),
        sa.Column("y", sa.Float(), server_default="0", nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("rotation", sa.Float(), server_default="0", nullable=False),
        sa.Column("z_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("visible", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("locked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["linked_character_id"], ["characters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_tokens_id"), "room_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_room_tokens_room_id"), "room_tokens", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_tokens_asset_id"), "room_tokens", ["asset_id"], unique=False)
    op.create_index(
        op.f("ix_room_tokens_linked_character_id"),
        "room_tokens",
        ["linked_character_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_room_tokens_owner_user_id"),
        "room_tokens",
        ["owner_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_room_tokens_owner_user_id"), table_name="room_tokens")
    op.drop_index(op.f("ix_room_tokens_linked_character_id"), table_name="room_tokens")
    op.drop_index(op.f("ix_room_tokens_asset_id"), table_name="room_tokens")
    op.drop_index(op.f("ix_room_tokens_room_id"), table_name="room_tokens")
    op.drop_index(op.f("ix_room_tokens_id"), table_name="room_tokens")
    op.drop_table("room_tokens")
