"""refactor room_maps: replace asset_id with library_resource_id, drop grid fields

Revision ID: 20260608_0018
Revises: 20260608_0017
Create Date: 2026-06-08
"""

import sqlalchemy as sa
from alembic import op

revision = "20260608_0018"
down_revision = "20260608_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Clear existing room_maps data since we can't backfill library_resource_id
    # for rows created via the old direct-upload path.
    op.execute("DELETE FROM room_maps")

    # Drop the old asset_id index before batch-rebuilding the table;
    # otherwise batch mode will try to recreate it on the new schema (which has no asset_id).
    op.drop_index("ix_room_maps_asset_id", table_name="room_maps")

    # SQLite doesn't support ALTER TABLE ADD COLUMN with FK constraints;
    # use batch mode (copy-and-move) to rebuild the table.
    with op.batch_alter_table("room_maps") as batch_op:
        batch_op.add_column(
            sa.Column("library_resource_id", sa.Integer(), nullable=False, server_default="0"),
        )
        batch_op.drop_column("asset_id")
        batch_op.drop_column("map_grid_x")
        batch_op.drop_column("map_grid_y")
        batch_op.drop_column("map_grid_size")
        batch_op.create_foreign_key(
            "fk_room_maps_library_resource_id",
            "library_resources",
            ["library_resource_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index("ix_room_maps_library_resource_id", ["library_resource_id"])


def downgrade() -> None:
    with op.batch_alter_table("room_maps") as batch_op:
        batch_op.drop_index("ix_room_maps_library_resource_id")
        batch_op.drop_constraint("fk_room_maps_library_resource_id", type_="foreignkey")
        batch_op.drop_column("library_resource_id")
        batch_op.add_column(sa.Column("asset_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("map_grid_x", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("map_grid_y", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("map_grid_size", sa.Float(), nullable=True))

    op.create_index("ix_room_maps_asset_id", "room_maps", ["asset_id"])
