from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.rooms.models import RoomDiceRoll, RoomMember, RoomScene, RoomToken
from app.modules.rooms.constants import GameRole


class RoomDiceRepository:
    async def create_roll(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        roller_user_id: int,
        actor_type: str,
        actor_token_id: int | None,
        actor_display_name: str,
        actor_asset_id: int | None,
        label: str,
        formula: str,
        visibility: str,
        total: int,
        detail: dict,
    ) -> RoomDiceRoll:
        roll = RoomDiceRoll(
            room_id=room_id,
            scene_id=scene_id,
            roller_user_id=roller_user_id,
            actor_type=actor_type,
            actor_token_id=actor_token_id,
            actor_display_name=actor_display_name,
            actor_asset_id=actor_asset_id,
            label=label,
            formula=formula,
            visibility=visibility,
            total=total,
            detail=detail,
        )
        db.add(roll)
        await db.flush()
        await db.refresh(roll)
        return roll

    async def find_roll_by_id(self, db: AsyncSession, roll_id: int) -> RoomDiceRoll | None:
        result = await db.execute(select(RoomDiceRoll).where(RoomDiceRoll.id == roll_id))
        return result.scalar_one_or_none()

    async def get_rolls_by_scene_id(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        before_id: int | None = None,
        limit: int = 30,
        include_blind: bool = True,
    ) -> list[RoomDiceRoll]:
        stmt = (
            select(RoomDiceRoll)
            .where(RoomDiceRoll.room_id == room_id, RoomDiceRoll.scene_id == scene_id)
            .order_by(desc(RoomDiceRoll.id))
            .limit(limit)
        )
        if not include_blind:
            stmt = stmt.where(RoomDiceRoll.visibility != "blind")
        if before_id is not None:
            stmt = stmt.where(RoomDiceRoll.id < before_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def find_active_scene(self, db: AsyncSession, *, room_id: int) -> RoomScene | None:
        result = await db.execute(
            select(RoomScene)
            .where(RoomScene.room_id == room_id, RoomScene.is_active.is_(True))
            .order_by(RoomScene.id)
        )
        return result.scalar_one_or_none()

    async def find_scene(self, db: AsyncSession, *, room_id: int, scene_id: int) -> RoomScene | None:
        result = await db.execute(
            select(RoomScene).where(RoomScene.room_id == room_id, RoomScene.id == scene_id)
        )
        return result.scalar_one_or_none()

    async def create_default_scene(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        snapshot: dict,
    ) -> RoomScene:
        scene = RoomScene(
            room_id=room_id,
            name="默认场景",
            snapshot=snapshot,
            is_active=True,
            created_by_user_id=None,
        )
        db.add(scene)
        await db.flush()
        await db.refresh(scene)
        return scene

    async def find_token(self, db: AsyncSession, *, room_id: int, token_id: int) -> RoomToken | None:
        result = await db.execute(
            select(RoomToken)
            .where(RoomToken.room_id == room_id, RoomToken.id == token_id)
            .options(selectinload(RoomToken.owner), selectinload(RoomToken.library_resource))
        )
        return result.scalar_one_or_none()

    async def get_gm_user_ids(self, db: AsyncSession, *, room_id: int) -> list[int]:
        result = await db.execute(
            select(RoomMember.user_id).where(
                RoomMember.room_id == room_id,
                RoomMember.game_role == GameRole.GM.value,
            )
        )
        return list(result.scalars().all())
