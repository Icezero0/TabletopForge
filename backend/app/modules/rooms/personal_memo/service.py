from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import ForbiddenError
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomPersonalMemo
from app.modules.rooms.personal_memo.repository import RoomPersonalMemoRepository
from app.modules.rooms.room.service import RoomService
from app.modules.users.models import User


class RoomPersonalMemoService:
    def __init__(self) -> None:
        self.repo = RoomPersonalMemoRepository()
        self.membership_service = RoomMembershipService()
        self.room_service = RoomService()

    async def _require_room_member(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
    ) -> None:
        await self.room_service.get_room_by_id(db, room_id)
        member = await self.membership_service.find_room_member(
            db,
            room_id=room_id,
            user_id=user.id,
        )
        if member is None:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"room_id": room_id},
            )

    async def get_personal_memo(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
    ) -> RoomPersonalMemo:
        await self._require_room_member(db, room_id=room_id, user=user)
        memo = await self.repo.get_memo(db, room_id=room_id, user_id=user.id)
        if memo is not None:
            return memo
        return RoomPersonalMemo(
            id=0,
            user_id=user.id,
            room_id=room_id,
            content="",
            updated_at=None,
        )

    async def put_personal_memo(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        content: str,
    ) -> RoomPersonalMemo:
        await self._require_room_member(db, room_id=room_id, user=user)
        memo = await self.repo.upsert_memo(
            db,
            room_id=room_id,
            user_id=user.id,
            content=content,
        )
        await db.commit()
        return memo
