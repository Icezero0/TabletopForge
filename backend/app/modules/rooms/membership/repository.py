from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.rooms.constants import GameRole
from app.modules.rooms.models import RoomMember


class RoomMembershipRepository:
    async def create_member(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
        role: str,
        game_role: str,
    ) -> RoomMember:
        member = RoomMember(
            room_id=room_id,
            user_id=user_id,
            role=role,
            game_role=game_role,
        )
        db.add(member)
        await db.flush()
        await db.refresh(member)
        return member

    async def get_member(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
    ) -> RoomMember | None:
        result = await db.execute(
            select(RoomMember)
            .where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
            .options(selectinload(RoomMember.user))
        )
        return result.scalar_one_or_none()

    async def get_members_by_room_id(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> list[RoomMember]:
        result = await db.execute(
            select(RoomMember)
            .where(RoomMember.room_id == room_id)
            .order_by(RoomMember.joined_at.asc(), RoomMember.user_id.asc())
            .options(selectinload(RoomMember.user))
        )
        return list(result.scalars().all())

    async def get_members_by_user_id(
        self,
        db: AsyncSession,
        *,
        user_id: int,
    ) -> list[RoomMember]:
        result = await db.execute(
            select(RoomMember).where(RoomMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def user_is_gm_in_any_room(
        self,
        db: AsyncSession,
        *,
        user_id: int,
    ) -> bool:
        result = await db.execute(
            select(RoomMember.id)
            .where(
                RoomMember.user_id == user_id,
                RoomMember.game_role == GameRole.GM.value,
            )
            .limit(1)
        )
        return result.first() is not None

    async def delete_members_by_room_and_user_id(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
    ) -> None:
        await db.execute(
            delete(RoomMember).where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id
            )
        )
        await db.flush()

    async def update_member_role(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
        role: str,
    ) -> RoomMember | None:
        await db.execute(
            update(RoomMember)
            .where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
            .values(role=role)
        )
        await db.flush()
        return await self.get_member(db, room_id=room_id, user_id=user_id)

    async def update_member_game_role(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
        game_role: str,
    ) -> RoomMember | None:
        await db.execute(
            update(RoomMember)
            .where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
            .values(game_role=game_role)
        )
        await db.flush()
        return await self.get_member(db, room_id=room_id, user_id=user_id)

    async def update_member_player_color(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
        player_color: str,
    ) -> RoomMember | None:
        await db.execute(
            update(RoomMember)
            .where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
            .values(player_color=player_color)
        )
        await db.flush()
        return await self.get_member(db, room_id=room_id, user_id=user_id)
