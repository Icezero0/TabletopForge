"""drop kind from characters and room_characters

Revision ID: 20260608_0016
Revises: 20260607_0015
Create Date: 2026-06-08
"""

from alembic import op

revision = "20260608_0016"
down_revision = "20260607_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("characters", "kind")
    op.drop_column("room_characters", "kind")


def downgrade() -> None:
    import sqlalchemy as sa
    op.add_column("characters", sa.Column("kind", sa.String(16), nullable=False, server_default="pc_main"))
    op.add_column("room_characters", sa.Column("kind", sa.String(16), nullable=False, server_default="pc_main"))
