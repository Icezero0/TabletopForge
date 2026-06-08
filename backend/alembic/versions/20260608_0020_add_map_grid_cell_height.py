"""add map_grid_cell_height to library_resources for non-square grid support

Revision ID: 20260608_0020
Revises: 20260608_0019
Create Date: 2026-06-08
"""

import sqlalchemy as sa
from alembic import op

revision = "20260608_0020"
down_revision = "20260608_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("library_resources", sa.Column("map_grid_cell_height", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("library_resources") as batch_op:
        batch_op.drop_column("map_grid_cell_height")
