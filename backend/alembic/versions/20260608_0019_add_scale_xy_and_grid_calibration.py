"""add scale_x/scale_y to room_maps; add map_grid_calibration to library_resources

Revision ID: 20260608_0019
Revises: 20260608_0018
Create Date: 2026-06-08
"""

import sqlalchemy as sa
from alembic import op

revision = "20260608_0019"
down_revision = "20260608_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite supports ADD COLUMN for nullable columns without FK constraints.
    op.add_column("room_maps", sa.Column("scale_x", sa.Float(), nullable=True))
    op.add_column("room_maps", sa.Column("scale_y", sa.Float(), nullable=True))

    op.add_column("library_resources", sa.Column("map_grid_calibration", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("room_maps") as batch_op:
        batch_op.drop_column("scale_x")
        batch_op.drop_column("scale_y")

    with op.batch_alter_table("library_resources") as batch_op:
        batch_op.drop_column("map_grid_calibration")
