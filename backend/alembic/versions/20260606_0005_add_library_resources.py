"""add library_resources table

Revision ID: 20260606_0005
Revises: 20260604_0004
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0005"
down_revision: str | None = "20260604_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "library_resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("primary_asset_id", sa.Integer(), nullable=True),
        sa.Column("meta", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("usage_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_asset_id"], ["assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_library_resources_id"), "library_resources", ["id"], unique=False)
    op.create_index(
        op.f("ix_library_resources_owner_id"), "library_resources", ["owner_id"], unique=False
    )
    op.create_index(
        op.f("ix_library_resources_primary_asset_id"),
        "library_resources",
        ["primary_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_library_resources_type"), "library_resources", ["type"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_library_resources_type"), table_name="library_resources")
    op.drop_index(
        op.f("ix_library_resources_primary_asset_id"), table_name="library_resources"
    )
    op.drop_index(op.f("ix_library_resources_owner_id"), table_name="library_resources")
    op.drop_index(op.f("ix_library_resources_id"), table_name="library_resources")
    op.drop_table("library_resources")
