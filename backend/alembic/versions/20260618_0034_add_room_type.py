"""add room type

Revision ID: 20260618_0034
Revises: 20260614_0033
Create Date: 2026-06-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260618_0034"
down_revision: str | None = "20260614_0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("rooms") as batch_op:
        batch_op.add_column(
            sa.Column("type", sa.String(length=32), server_default="DND5E", nullable=False)
        )
        batch_op.create_index("ix_rooms_type", ["type"])


def downgrade() -> None:
    with op.batch_alter_table("rooms") as batch_op:
        batch_op.drop_index("ix_rooms_type")
        batch_op.drop_column("type")
