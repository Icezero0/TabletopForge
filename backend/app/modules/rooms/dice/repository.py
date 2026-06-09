from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.rooms.models import RoomDiceRoll, RoomMember, RoomToken
from app.modules.rooms.constants import GameRole


class RoomDiceRepository:
    async def create_roll(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        roller_user_id: int,
        actor_type: str,
        actor_token_id: int | None,
        actor_display_name: str,
        label: str,
        formula: str,
        visibility: str,
        total: int,
        detail: dict,
    ) -> RoomDiceRoll:
        roll = RoomDiceRoll(
            room_id=room_id,
            roller_user_id=roller_user_id,
            actor_type=actor_type,
            actor_token_id=actor_token_id,
            actor_display_name=actor_display_name,
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

    async def get_rolls_by_room_id(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        before_id: int | None = None,
        limit: int = 30,
        include_blind: bool = True,
    ) -> list[RoomDiceRoll]:
        stmt = (
            select(RoomDiceRoll)
            .where(RoomDiceRoll.room_id == room_id)
            .order_by(desc(RoomDiceRoll.id))
            .limit(limit)
        )
        if not include_blind:
            stmt = stmt.where(RoomDiceRoll.visibility != "blind")
        if before_id is not None:
            stmt = stmt.where(RoomDiceRoll.id < before_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def find_token(self, db: AsyncSession, *, room_id: int, token_id: int) -> RoomToken | None:
        result = await db.execute(
            select(RoomToken)
            .where(RoomToken.room_id == room_id, RoomToken.id == token_id)
            .options(selectinload(RoomToken.owner))
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
