"""let room tokens survive deleted token resources

Revision ID: 20260614_0032
Revises: 20260614_0031
Create Date: 2026-06-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260614_0032"
down_revision: str | None = "20260614_0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("room_tokens") as batch_op:
        batch_op.drop_constraint("fk_room_tokens_library_resource_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_room_tokens_library_resource_id",
            "library_resources",
            ["library_resource_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("room_tokens") as batch_op:
        batch_op.drop_constraint("fk_room_tokens_library_resource_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_room_tokens_library_resource_id",
            "library_resources",
            ["library_resource_id"],
            ["id"],
            ondelete="RESTRICT",
        )
