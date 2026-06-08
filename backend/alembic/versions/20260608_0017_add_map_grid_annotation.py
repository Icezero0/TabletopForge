"""add map grid annotation fields to library_resources and room_maps

Revision ID: 20260608_0017
Revises: 20260608_0016
Create Date: 2026-06-08
"""

import sqlalchemy as sa
from alembic import op

revision = "20260608_0017"
down_revision = "20260608_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("library_resources", sa.Column("map_grid_x", sa.Float(), nullable=True))
    op.add_column("library_resources", sa.Column("map_grid_y", sa.Float(), nullable=True))
    op.add_column("library_resources", sa.Column("map_grid_size", sa.Float(), nullable=True))
    op.add_column("room_maps", sa.Column("map_grid_x", sa.Float(), nullable=True))
    op.add_column("room_maps", sa.Column("map_grid_y", sa.Float(), nullable=True))
    op.add_column("room_maps", sa.Column("map_grid_size", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("library_resources", "map_grid_x")
    op.drop_column("library_resources", "map_grid_y")
    op.drop_column("library_resources", "map_grid_size")
    op.drop_column("room_maps", "map_grid_x")
    op.drop_column("room_maps", "map_grid_y")
    op.drop_column("room_maps", "map_grid_size")
