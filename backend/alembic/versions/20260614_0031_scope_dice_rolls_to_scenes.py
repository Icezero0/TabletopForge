"""scope dice rolls to scenes

Revision ID: 20260614_0031
Revises: 20260614_0030
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260614_0031"
down_revision: str | None = "20260614_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


EMPTY_SCENE_SNAPSHOT = {
    "settings": {
        "grid_cell_ft": 5,
        "grid_cell_px": 40,
        "combat_state": None,
        "music_state": None,
        "fog_state": None,
    },
    "maps": [],
    "drawings": [],
    "tokens": [],
    "characters": [],
}


def upgrade() -> None:
    connection = op.get_bind()

    room_scenes = sa.table(
        "room_scenes",
        sa.column("room_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("snapshot", sa.JSON),
        sa.column("is_active", sa.Boolean),
        sa.column("created_by_user_id", sa.Integer),
    )

    missing_scene_room_ids = [
        row[0]
        for row in connection.execute(
            sa.text(
                """
                SELECT rooms.id
                FROM rooms
                LEFT JOIN room_scenes ON room_scenes.room_id = rooms.id
                WHERE room_scenes.id IS NULL
                """
            )
        )
    ]
    if missing_scene_room_ids:
        connection.execute(
            room_scenes.insert(),
            [
                {
                    "room_id": room_id,
                    "name": "默认场景",
                    "snapshot": EMPTY_SCENE_SNAPSHOT,
                    "is_active": True,
                    "created_by_user_id": None,
                }
                for room_id in missing_scene_room_ids
            ],
        )

    op.add_column("room_dice_rolls", sa.Column("scene_id", sa.Integer(), nullable=True))
    op.add_column("room_dice_rolls", sa.Column("actor_asset_id", sa.Integer(), nullable=True))

    connection.execute(
        sa.text(
            """
            UPDATE room_dice_rolls
            SET scene_id = (
                SELECT room_scenes.id
                FROM room_scenes
                WHERE room_scenes.room_id = room_dice_rolls.room_id
                ORDER BY room_scenes.is_active DESC, room_scenes.id ASC
                LIMIT 1
            )
            WHERE scene_id IS NULL
            """
        )
    )

    with op.batch_alter_table("room_dice_rolls") as batch_op:
        batch_op.alter_column("scene_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_room_dice_rolls_scene_id_room_scenes",
            "room_scenes",
            ["scene_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(op.f("ix_room_dice_rolls_scene_id"), ["scene_id"], unique=False)
        batch_op.create_index(op.f("ix_room_dice_rolls_actor_asset_id"), ["actor_asset_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("room_dice_rolls") as batch_op:
        batch_op.drop_index(op.f("ix_room_dice_rolls_actor_asset_id"))
        batch_op.drop_index(op.f("ix_room_dice_rolls_scene_id"))
        batch_op.drop_constraint("fk_room_dice_rolls_scene_id_room_scenes", type_="foreignkey")
        batch_op.drop_column("actor_asset_id")
        batch_op.drop_column("scene_id")
