"""migrate character kinds to pc_main / pc_additional / npc

Revision ID: 20260606_0012
Revises: 20260606_0011
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260606_0012"
down_revision: str | None = "20260606_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # room_characters: pc → pc_main, monster → npc
    op.execute("UPDATE room_characters SET kind = 'pc_main' WHERE kind = 'pc'")
    op.execute("UPDATE room_characters SET kind = 'npc' WHERE kind = 'monster'")
    # additional + added_by is GM in same room → npc
    op.execute(
        """
        UPDATE room_characters
        SET kind = 'npc'
        WHERE kind = 'additional'
          AND EXISTS (
            SELECT 1 FROM room_members rm
            WHERE rm.room_id = room_characters.room_id
              AND rm.user_id = room_characters.added_by_user_id
              AND rm.game_role = 'GM'
          )
        """
    )
    op.execute(
        "UPDATE room_characters SET kind = 'pc_additional' WHERE kind = 'additional'"
    )

    # characters: pc → pc_main, monster → npc
    op.execute("UPDATE characters SET kind = 'pc_main' WHERE kind = 'pc'")
    op.execute("UPDATE characters SET kind = 'npc' WHERE kind = 'monster'")
    op.execute(
        """
        UPDATE characters
        SET kind = 'npc'
        WHERE kind = 'additional'
          AND EXISTS (
            SELECT 1 FROM room_members rm
            WHERE rm.user_id = characters.owner_id
              AND rm.game_role = 'GM'
          )
        """
    )
    op.execute(
        "UPDATE characters SET kind = 'pc_additional' WHERE kind = 'additional'"
    )
    # sync global kind from room_characters when linked
    op.execute(
        """
        UPDATE characters
        SET kind = (
          SELECT rc.kind FROM room_characters rc
          WHERE rc.character_id = characters.id
          ORDER BY rc.id
          LIMIT 1
        )
        WHERE EXISTS (
          SELECT 1 FROM room_characters rc
          WHERE rc.character_id = characters.id
        )
        """
    )

    with op.batch_alter_table("characters") as batch_op:
        batch_op.alter_column("kind", server_default="pc_main")


def downgrade() -> None:
    op.execute(
        """
        UPDATE room_characters
        SET kind = 'additional'
        WHERE kind IN ('npc', 'pc_additional')
        """
    )
    op.execute("UPDATE room_characters SET kind = 'pc' WHERE kind = 'pc_main'")

    op.execute(
        """
        UPDATE characters
        SET kind = 'additional'
        WHERE kind IN ('npc', 'pc_additional')
        """
    )
    op.execute("UPDATE characters SET kind = 'pc' WHERE kind = 'pc_main'")

    with op.batch_alter_table("characters") as batch_op:
        batch_op.alter_column("kind", server_default="pc")
