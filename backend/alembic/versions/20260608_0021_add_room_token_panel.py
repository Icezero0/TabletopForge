"""add panel JSON column to room_tokens for per-instance state

Revision ID: 20260608_0021
Revises: 20260608_0020
Create Date: 2026-06-08
"""

import sqlalchemy as sa
from alembic import op

revision = "20260608_0021"
down_revision = "20260608_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("room_tokens", sa.Column("panel", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("room_tokens") as batch_op:
        batch_op.drop_column("panel")
