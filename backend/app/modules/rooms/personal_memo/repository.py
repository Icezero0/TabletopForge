from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rooms.models import RoomPersonalMemo


class RoomPersonalMemoRepository:
    async def get_memo(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
    ) -> RoomPersonalMemo | None:
        result = await db.execute(
            select(RoomPersonalMemo).where(
                RoomPersonalMemo.room_id == room_id,
                RoomPersonalMemo.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_memo(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
        content: str,
    ) -> RoomPersonalMemo:
        memo = await self.get_memo(db, room_id=room_id, user_id=user_id)
        if memo is None:
            memo = RoomPersonalMemo(
                room_id=room_id,
                user_id=user_id,
                content=content,
            )
            db.add(memo)
        else:
            memo.content = content
        await db.flush()
        await db.refresh(memo)
        return memo
