"""add room tabletop tables

Revision ID: 20260604_0004
Revises: 20260604_0003
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0004"
down_revision: str | None = "20260605_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "room_tabletop_settings",
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("grid_cell_ft", sa.Float(), server_default="5", nullable=False),
        sa.Column("grid_cell_px", sa.Integer(), server_default="40", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("room_id"),
    )
    op.create_table(
        "room_maps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("x", sa.Float(), server_default="0", nullable=False),
        sa.Column("y", sa.Float(), server_default="0", nullable=False),
        sa.Column("scale", sa.Float(), server_default="1", nullable=False),
        sa.Column("locked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("z_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_maps_id"), "room_maps", ["id"], unique=False)
    op.create_index(op.f("ix_room_maps_room_id"), "room_maps", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_maps_asset_id"), "room_maps", ["asset_id"], unique=False)
    op.create_table(
        "room_drawings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=False),
        sa.Column("style", sa.JSON(), nullable=False),
        sa.Column("z_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_drawings_id"), "room_drawings", ["id"], unique=False)
    op.create_index(op.f("ix_room_drawings_room_id"), "room_drawings", ["room_id"], unique=False)
    op.create_index(
        op.f("ix_room_drawings_created_by_user_id"),
        "room_drawings",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_room_drawings_created_by_user_id"), table_name="room_drawings")
    op.drop_index(op.f("ix_room_drawings_room_id"), table_name="room_drawings")
    op.drop_index(op.f("ix_room_drawings_id"), table_name="room_drawings")
    op.drop_table("room_drawings")
    op.drop_index(op.f("ix_room_maps_asset_id"), table_name="room_maps")
    op.drop_index(op.f("ix_room_maps_room_id"), table_name="room_maps")
    op.drop_index(op.f("ix_room_maps_id"), table_name="room_maps")
    op.drop_table("room_maps")
    op.drop_table("room_tabletop_settings")
