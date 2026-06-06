"""add character_states table

Revision ID: 20260606_0009
Revises: 20260606_0008
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0009"
down_revision: str | None = "20260606_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "character_states",
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column("current_hp", sa.Integer(), nullable=True),
        sa.Column("max_hp", sa.Integer(), nullable=True),
        sa.Column("temp_hp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("armor_class", sa.Integer(), nullable=True),
        sa.Column("conditions", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("damage_taken", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("character_id"),
    )


def downgrade() -> None:
    op.drop_table("character_states")
