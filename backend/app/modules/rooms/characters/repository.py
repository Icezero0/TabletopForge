from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.character.models import Character
from app.modules.rooms.constants import GameRole
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomCharacter, RoomMember


class RoomCharacterRepository:
    def __init__(self) -> None:
        self.membership_service = RoomMembershipService()

    async def create(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        character_id: int,
        added_by_user_id: int,
    ) -> RoomCharacter:
        entry = RoomCharacter(
            room_id=room_id,
            character_id=character_id,
            added_by_user_id=added_by_user_id,
        )
        db.add(entry)
        await db.flush()
        await db.refresh(entry)
        return entry

    async def list_by_room(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> list[RoomCharacter]:
        result = await db.execute(
            select(RoomCharacter)
            .where(RoomCharacter.room_id == room_id)
            .options(
                selectinload(RoomCharacter.character).selectinload(Character.state)
            )
            .order_by(RoomCharacter.created_at, RoomCharacter.id)
        )
        return list(result.scalars().all())

    async def get_by_room_and_character(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        character_id: int,
    ) -> RoomCharacter | None:
        result = await db.execute(
            select(RoomCharacter)
            .where(
                RoomCharacter.room_id == room_id,
                RoomCharacter.character_id == character_id,
            )
            .options(
                selectinload(RoomCharacter.character).selectinload(Character.state)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_room(
        self,
        db: AsyncSession,
        *,
        room_character_id: int,
        room_id: int,
    ) -> RoomCharacter | None:
        result = await db.execute(
            select(RoomCharacter)
            .where(
                RoomCharacter.id == room_character_id,
                RoomCharacter.room_id == room_id,
            )
            .options(
                selectinload(RoomCharacter.character).selectinload(Character.state)
            )
        )
        return result.scalar_one_or_none()

    async def set_visibility(
        self,
        db: AsyncSession,
        *,
        room_character_id: int,
        is_hidden: bool,
    ) -> RoomCharacter:
        result = await db.execute(
            select(RoomCharacter)
            .where(RoomCharacter.id == room_character_id)
            .options(
                selectinload(RoomCharacter.character).selectinload(Character.state)
            )
        )
        entry = result.scalar_one()
        entry.is_hidden = is_hidden
        await db.flush()
        await db.refresh(entry)
        return entry

    async def delete_by_id_and_room(
        self,
        db: AsyncSession,
        *,
        room_character_id: int,
        room_id: int,
    ) -> bool:
        result = await db.execute(
            select(RoomCharacter).where(
                RoomCharacter.id == room_character_id,
                RoomCharacter.room_id == room_id,
            )
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            return False
        await db.delete(entry)
        return True

    async def is_character_in_room(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        room_id: int,
    ) -> bool:
        result = await db.execute(
            select(RoomCharacter.id).where(
                RoomCharacter.character_id == character_id,
                RoomCharacter.room_id == room_id,
            )
        )
        return result.first() is not None

    async def list_room_ids_for_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> list[int]:
        result = await db.execute(
            select(RoomCharacter.room_id).where(
                RoomCharacter.character_id == character_id,
            )
        )
        return [row[0] for row in result.all()]

    async def user_game_role_for_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user_id: int,
    ) -> GameRole | None:
        result = await db.execute(
            select(RoomMember.game_role)
            .join(RoomCharacter, RoomCharacter.room_id == RoomMember.room_id)
            .where(
                RoomCharacter.character_id == character_id,
                RoomMember.user_id == user_id,
            )
        )
        row = result.first()
        if row is None:
            return None
        return GameRole(row[0])

    async def user_can_read_character_token_image(
        self,
        db: AsyncSession,
        *,
        asset_id: int,
        user_id: int,
    ) -> bool:
        result = await db.execute(
            select(RoomMember.room_id)
            .join(RoomCharacter, RoomCharacter.room_id == RoomMember.room_id)
            .join(Character, Character.id == RoomCharacter.character_id)
            .where(
                Character.token_image_asset_id == asset_id,
                RoomMember.user_id == user_id,
            )
        )
        return result.first() is not None

    async def is_owner_gm_in_room(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        owner_id: int,
    ) -> bool:
        role = await self.membership_service.find_game_role(
            db,
            room_id=room_id,
            user_id=owner_id,
        )
        return role == GameRole.GM

    async def character_owner_is_gm_in_any_room(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        owner_id: int,
    ) -> bool:
        room_ids = await self.list_room_ids_for_character(
            db,
            character_id=character_id,
        )
        for room_id in room_ids:
            if await self.is_owner_gm_in_room(
                db,
                room_id=room_id,
                owner_id=owner_id,
            ):
                return True
        return False
