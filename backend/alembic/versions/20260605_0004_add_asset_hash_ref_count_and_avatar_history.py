"""add asset hash/ref count and user avatar history

Revision ID: 20260605_0004
Revises: 20260604_0003
Create Date: 2026-06-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260605_0004"
down_revision: str | None = "20260604_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LEGACY_CONTENT_HASH = "0" * 64


def upgrade() -> None:
    op.add_column("assets", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column(
        "assets",
        sa.Column("ref_count", sa.Integer(), server_default="1", nullable=False),
    )
    op.execute(
        sa.text("UPDATE assets SET content_hash = :content_hash WHERE content_hash IS NULL")
        .bindparams(content_hash=LEGACY_CONTENT_HASH)
    )

    with op.batch_alter_table("assets") as batch_op:
        batch_op.alter_column(
            "content_hash",
            existing_type=sa.String(length=64),
            nullable=False,
        )

    op.create_index(
        "idx_assets_type_hash_size_content_type",
        "assets",
        ["asset_type", "content_hash", "size_bytes", "content_type"],
        unique=False,
    )
    op.create_index(op.f("ix_assets_content_hash"), "assets", ["content_hash"], unique=False)

    op.create_table(
        "user_avatar_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_avatar_history_asset_id"), "user_avatar_history", ["asset_id"], unique=False)
    op.create_index(op.f("ix_user_avatar_history_id"), "user_avatar_history", ["id"], unique=False)
    op.create_index(op.f("ix_user_avatar_history_user_id"), "user_avatar_history", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_avatar_history_user_id"), table_name="user_avatar_history")
    op.drop_index(op.f("ix_user_avatar_history_id"), table_name="user_avatar_history")
    op.drop_index(op.f("ix_user_avatar_history_asset_id"), table_name="user_avatar_history")
    op.drop_table("user_avatar_history")

    op.drop_index(op.f("ix_assets_content_hash"), table_name="assets")
    op.drop_index("idx_assets_type_hash_size_content_type", table_name="assets")
    op.drop_column("assets", "ref_count")
    op.drop_column("assets", "content_hash")
