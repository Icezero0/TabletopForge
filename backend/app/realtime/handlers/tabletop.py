from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.character.repository import CharacterRepository
from app.modules.users.repository import UserRepository
from app.realtime.manager import RealtimeManager, WsConnection
from app.realtime.protocol import WsCommandPayload
from app.realtime.publisher import RealtimePublisher


class TabletopCommandHandler:
    def __init__(self) -> None:
        self.membership_service = RoomMembershipService()
        self.user_repo = UserRepository()
        self.tabletop_repo = RoomTabletopRepository()
        self.character_repo = CharacterRepository()

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

        if command.action == WsCommandAction.TOKEN_TRANSFORM_PREVIEW:
            await self._handle_token_transform_preview(
                db=db,
                publisher=publisher,
                connection=connection,
                command=command,
            )
            return

        if command.action == WsCommandAction.OBJECT_SELECTION:
            await self._handle_object_selection(
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

    async def _require_token_room(
        self,
        db: AsyncSession,
        *,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> tuple[int, GameRole]:
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
        return room_id, game_role

    async def _require_token_transform_access(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        token_id: int,
        user_id: int,
        game_role: GameRole,
    ) -> None:
        token = await self.tabletop_repo.get_token(db, token_id=token_id, room_id=room_id)
        if token is None:
            raise BadRequestError(
                "Token not found",
                reason=ErrorReason.BAD_REQUEST,
                details={"token_id": token_id},
            )
        if token.locked:
            raise BadRequestError(
                "Token is locked",
                reason=ErrorReason.BAD_REQUEST,
                details={"token_id": token_id},
            )

        if game_role == GameRole.GM:
            require_game_permission(game_role, GamePermission.MANAGE_ANY_TOKEN)
            return

        if game_role == GameRole.PL:
            require_game_permission(game_role, GamePermission.MOVE_OWN_CHARACTER_TOKEN)
            character = await self.character_repo.get_by_id(
                db,
                character_id=token.linked_character_id,
            )
            if character is not None and character.owner_id == user_id:
                return

        raise ForbiddenError(
            "You do not have permission to perform this action",
            reason=ErrorReason.ROOM_PERMISSION_DENIED,
            details={"token_id": token_id},
        )

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
            x = float(data["x"] if data.get("x") is not None else data["x1"])
            y = float(data["y"] if data.get("y") is not None else data["y1"])
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
            x=x,
            y=y,
        )

    async def _handle_token_transform_preview(
        self,
        *,
        db: AsyncSession,
        publisher: RealtimePublisher,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> None:
        room_id, game_role = await self._require_token_room(
            db,
            connection=connection,
            command=command,
        )
        data = command.data or {}
        try:
            token_id = int(data["token_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BadRequestError(
                "Invalid token transform payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            ) from exc

        transform: dict[str, float] = {}
        for key in ("x", "y", "width", "height"):
            if data.get(key) is not None:
                try:
                    transform[key] = float(data[key])
                except (TypeError, ValueError) as exc:
                    raise BadRequestError(
                        "Invalid token transform payload",
                        reason=ErrorReason.INVALID_PAYLOAD,
                    ) from exc
                if key in {"width", "height"} and transform[key] <= 0:
                    raise BadRequestError(
                        "Invalid token transform payload",
                        reason=ErrorReason.INVALID_PAYLOAD,
                    )

        if not transform:
            raise BadRequestError(
                "Invalid token transform payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            )

        await self._require_token_transform_access(
            db,
            room_id=room_id,
            token_id=token_id,
            user_id=connection.user_id,
            game_role=game_role,
        )
        await publisher.publish_token_transform_preview(
            room_id=room_id,
            token_id=token_id,
            transform=transform,
            user_id=connection.user_id,
            exclude_connection_ids={connection.connection_id},
        )

    async def _handle_object_selection(
        self,
        *,
        db: AsyncSession,
        publisher: RealtimePublisher,
        connection: WsConnection,
        command: WsCommandPayload,
    ) -> None:
        room_id = await self._require_pointer_room(
            db,
            connection=connection,
            command=command,
        )
        data = command.data or {}
        try:
            active = bool(data["active"])
            object_type = str(data.get("object_type") or "")
            raw_object_id = data.get("object_id")
            object_id = int(raw_object_id) if raw_object_id is not None else None
        except (KeyError, TypeError, ValueError) as exc:
            raise BadRequestError(
                "Invalid object selection payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            ) from exc

        if object_type not in {"token", "drawing"}:
            raise BadRequestError(
                "Invalid object selection payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            )
        if active and object_id is None:
            raise BadRequestError(
                "Invalid object selection payload",
                reason=ErrorReason.INVALID_PAYLOAD,
            )

        await publisher.publish_object_selection(
            room_id=room_id,
            user_id=connection.user_id,
            object_type=object_type,
            object_id=object_id,
            active=active,
            exclude_connection_ids={connection.connection_id},
        )
