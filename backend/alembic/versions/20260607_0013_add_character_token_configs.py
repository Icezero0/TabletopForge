"""add character_token_configs table

Revision ID: 20260607_0013
Revises: 20260606_0012
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260607_0013"
down_revision: str | None = "20260606_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "character_token_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("name", sa.String(length=100), server_default="", nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("panel_initial", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_character_token_configs_id"), "character_token_configs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_character_token_configs_character_id"),
        "character_token_configs",
        ["character_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_character_token_configs_character_id"), table_name="character_token_configs"
    )
    op.drop_index(
        op.f("ix_character_token_configs_id"), table_name="character_token_configs"
    )
    op.drop_table("character_token_configs")
