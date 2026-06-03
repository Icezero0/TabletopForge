from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rooms.models import RoomSettings


class RoomSettingsRepository:
    async def create_settings(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> RoomSettings:
        settings = RoomSettings(
            room_id=room_id,
        )
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
        return settings

    async def get_by_room_id(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> RoomSettings | None:
        result = await db.execute(
            select(RoomSettings).where(RoomSettings.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def save_settings(
        self,
        db: AsyncSession,
        settings: RoomSettings,
    ) -> RoomSettings:
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
        return settings
