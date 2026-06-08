"""refactor room_token: drop asset_id/token_type, add library_resource_id, make linked_character_id NOT NULL

Revision ID: 20260609_0022
Revises: 20260608_0021
Create Date: 2026-06-09
"""

import sqlalchemy as sa
from alembic import op

revision = "20260609_0022"
down_revision = "20260608_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop tokens with no linked character (incompatible with upcoming NOT NULL constraint)
    op.execute("DELETE FROM room_tokens WHERE linked_character_id IS NULL")

    # Drop asset_id index before batch rebuild
    op.drop_index("ix_room_tokens_asset_id", table_name="room_tokens")

    with op.batch_alter_table("room_tokens") as batch_op:
        # Add library_resource_id (nullable FK to library_resources)
        batch_op.add_column(
            sa.Column("library_resource_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_room_tokens_library_resource_id",
            "library_resources",
            ["library_resource_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index("ix_room_tokens_library_resource_id", ["library_resource_id"])

        # Drop asset_id column (FK removed implicitly via batch rebuild)
        batch_op.drop_column("asset_id")

        # Drop token_type column
        batch_op.drop_column("token_type")

        # Make linked_character_id NOT NULL with CASCADE
        # batch mode rebuilds the whole table, so the old SET NULL FK is gone;
        # just alter nullable and declare the new FK.
        batch_op.alter_column("linked_character_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_room_tokens_linked_character_id",
            "characters",
            ["linked_character_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    op.drop_index("ix_room_tokens_library_resource_id", table_name="room_tokens")

    with op.batch_alter_table("room_tokens") as batch_op:
        batch_op.drop_constraint("fk_room_tokens_linked_character_id", type_="foreignkey")
        batch_op.alter_column("linked_character_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_foreign_key(
            "fk_room_tokens_linked_character_id",
            "characters",
            ["linked_character_id"],
            ["id"],
            ondelete="SET NULL",
        )

        batch_op.drop_constraint("fk_room_tokens_library_resource_id", type_="foreignkey")
        batch_op.drop_column("library_resource_id")

        batch_op.add_column(
            sa.Column("token_type", sa.String(16), nullable=False, server_default="character")
        )
        batch_op.add_column(sa.Column("asset_id", sa.Integer(), nullable=True))

    op.create_index("ix_room_tokens_asset_id", "room_tokens", ["asset_id"])
