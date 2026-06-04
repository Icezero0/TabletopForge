from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError
from app.modules.rooms.constants import GamePermission
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.users.repository import UserRepository
from app.realtime.manager import RealtimeManager, WsConnection
from app.realtime.protocol import WsCommandPayload
from app.realtime.publisher import RealtimePublisher


class TabletopCommandHandler:
    def __init__(self) -> None:
        self.membership_service = RoomMembershipService()
        self.user_repo = UserRepository()

    async def handle(
        self,
        *,
        db: AsyncSession,
        manager: RealtimeManager,
        publisher: RealtimePublisher,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> None:
        from app.realtime.constants import WsCommandAction

        if command.action == WsCommandAction.POINTER_PRESENCE:
            await self._handle_pointer_presence(
                db=db,
                publisher=publisher,
                connection=connection,
                command=command,
            )
            return

        if command.action == WsCommandAction.POINTER_LASER:
            await self._handle_pointer_laser(
                db=db,
                publisher=publisher,
                connection=connection,
                command=command,
            )
            return

        raise BadRequestError(
            f"Unsupported tabletop command action: {command.action}",
            reason=ErrorReason.UNSUPPORTED_COMMAND_ACTION,
            details={"action": command.action},
        )

    async def _require_pointer_room(
        self,
        db: AsyncSession,
        *,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> int:
        room_id = connection.active_room_id
        if room_id is None:
            raise BadRequestError(
                "Active room is required",
                reason=ErrorReason.BAD_REQUEST,
            )

        data = command.data or {}
        payload_room_id = data.get("room_id")
        if payload_room_id is not None and int(payload_room_id) != room_id:
            raise BadRequestError(
                "room_id does not match active room",
                reason=ErrorReason.BAD_REQUEST,
                details={"room_id": payload_room_id},
            )

        game_role = await self.membership_service.find_game_role(
            db,
            room_id=room_id,
            user_id=connection.user_id,
        )
        if game_role is None:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
            )
        require_game_permission(game_role, GamePermission.MANAGE_DRAWINGS)
        return room_id

    async def _display_name(self, db: AsyncSession, user_id: int) -> str:
        user = await self.user_repo.get_by_id(db, user_id)
        if user is None:
            return f"User {user_id}"
        return user.username or user.email or f"User {user_id}"

    async def _handle_pointer_presence(
        self,
        *,
        db: AsyncSession,
        publisher: RealtimePublisher,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> None:
        room_id = await self._require_pointer_room(db, connection=connection, command=command)
        data = command.data or {}
        try:
            x = float(data["x"])
            y = float(data["y"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BadRequestError(
                "Invalid pointer presence payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            ) from exc

        display_name = await self._display_name(db, connection.user_id)
        await publisher.publish_pointer_presence(
            room_id=room_id,
            user_id=connection.user_id,
            display_name=display_name,
            x=x,
            y=y,
            exclude_connection_ids={connection.connection_id},
        )

    async def _handle_pointer_laser(
        self,
        *,
        db: AsyncSession,
        publisher: RealtimePublisher,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> None:
        room_id = await self._require_pointer_room(db, connection=connection, command=command)
        data = command.data or {}
        try:
            active = bool(data["active"])
            x1 = float(data["x1"])
            y1 = float(data["y1"])
            x2 = float(data["x2"]) if data.get("x2") is not None else None
            y2 = float(data["y2"]) if data.get("y2") is not None else None
        except (KeyError, TypeError, ValueError) as exc:
            raise BadRequestError(
                "Invalid pointer laser payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            ) from exc

        display_name = await self._display_name(db, connection.user_id)
        await publisher.publish_pointer_laser(
            room_id=room_id,
            user_id=connection.user_id,
            display_name=display_name,
            active=active,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )
