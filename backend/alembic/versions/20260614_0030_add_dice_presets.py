"""add dice presets

Revision ID: 20260614_0030
Revises: 20260609_0029
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260614_0030"
down_revision = "20260609_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dice_presets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=16), server_default="preset", nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("formula", sa.String(length=255), server_default="", nullable=False),
        sa.Column("label", sa.String(length=255), server_default="", nullable=False),
        sa.Column("visibility", sa.String(length=16), server_default="public", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["dice_presets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dice_presets_id"), "dice_presets", ["id"], unique=False)
    op.create_index(op.f("ix_dice_presets_owner_id"), "dice_presets", ["owner_id"], unique=False)
    op.create_index(op.f("ix_dice_presets_parent_id"), "dice_presets", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_dice_presets_parent_id"), table_name="dice_presets")
    op.drop_index(op.f("ix_dice_presets_owner_id"), table_name="dice_presets")
    op.drop_index(op.f("ix_dice_presets_id"), table_name="dice_presets")
    op.drop_table("dice_presets")
