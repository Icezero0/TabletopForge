"""add characters table

Revision ID: 20260606_0006
Revises: 20260606_0005
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0006"
down_revision: str | None = "20260606_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("player_name", sa.String(length=255), server_default="", nullable=False),
        sa.Column("portrait_asset_id", sa.Integer(), nullable=True),
        sa.Column("system", sa.String(length=50), server_default="dnd5e", nullable=False),
        sa.Column("identity", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("flavor", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("attributes", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("features", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("spells", sa.JSON(), nullable=True),
        sa.Column("equipment", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("extras", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portrait_asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_characters_id"), "characters", ["id"], unique=False)
    op.create_index(op.f("ix_characters_owner_id"), "characters", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_characters_owner_id"), table_name="characters")
    op.drop_index(op.f("ix_characters_id"), table_name="characters")
    op.drop_table("characters")
