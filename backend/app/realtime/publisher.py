from typing import Any

from app.modules.messages.schemas import MessageResponse
from app.realtime.channels import ChannelKey, room_channel, user_channel
from app.realtime.constants import SessionCloseReason, WsEventType
from app.realtime.manager import RealtimeManager
from app.realtime.protocol import build_event_message
from app.realtime.state import PresenceState


class RealtimePublisher:
    def __init__(self, manager: RealtimeManager) -> None:
        self.manager = manager

    # =========================
    # internal helper
    # =========================

    async def _publish_event(
        self,
        *,
        channel: ChannelKey,
        event: WsEventType,
        data: dict[str, Any] | None = None,
        exclude_connection_ids: set[str] | None = None,
    ) -> None:
        await self.manager.publish(
            channel=channel,
            message=build_event_message(
                event=event,
                data=data,
            ),
            exclude_connection_ids=exclude_connection_ids,
        )

    # =========================
    # signal events
    # =========================

    async def publish_notification(
        self,
        *,
        user_id: int,
    ) -> None:
        await self._publish_event(
            channel=user_channel(user_id),
            event=WsEventType.NOTIFICATION,
            data=None,
        )

    async def publish_room_info(
        self,
        *,
        room_id: int,
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.ROOM_INFO,
            data=None,
        )

    async def publish_room_members(
        self,
        *,
        room_id: int,
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.ROOM_MEMBERS,
            data=None,
        )

    # =========================
    # data events
    # =========================

    async def publish_message(
        self,
        *,
        room_id: int,
        message: MessageResponse,
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.MESSAGE,
            data=message.model_dump(mode="json"),
        )

    async def publish_tabletop_settings_updated(
        self,
        *,
        room_id: int,
        settings: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.TABLETOP_SETTINGS_UPDATED,
            data={"room_id": room_id, "settings": settings},
        )

    async def publish_map_created(
        self,
        *,
        room_id: int,
        map_data: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.MAP_CREATED,
            data={"room_id": room_id, "map": map_data},
        )

    async def publish_map_updated(
        self,
        *,
        room_id: int,
        map_data: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.MAP_UPDATED,
            data={"room_id": room_id, "map": map_data},
        )

    async def publish_map_deleted(
        self,
        *,
        room_id: int,
        map_id: int,
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.MAP_DELETED,
            data={"room_id": room_id, "map_id": map_id},
        )

    async def publish_drawing_created(
        self,
        *,
        room_id: int,
        drawing: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.DRAWING_CREATED,
            data={"room_id": room_id, "drawing": drawing},
        )

    async def publish_drawing_updated(
        self,
        *,
        room_id: int,
        drawing: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.DRAWING_UPDATED,
            data={"room_id": room_id, "drawing": drawing},
        )

    async def publish_drawing_deleted(
        self,
        *,
        room_id: int,
        drawing_ids: list[int],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.DRAWING_DELETED,
            data={"room_id": room_id, "drawing_ids": drawing_ids},
        )

    async def publish_token_created(
        self,
        *,
        room_id: int,
        token: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.TOKEN_CREATED,
            data={"room_id": room_id, "token": token},
        )

    async def publish_token_updated(
        self,
        *,
        room_id: int,
        token: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.TOKEN_UPDATED,
            data={"room_id": room_id, "token": token},
        )

    async def publish_token_deleted(
        self,
        *,
        room_id: int,
        token_id: int,
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.TOKEN_DELETED,
            data={"room_id": room_id, "token_id": token_id},
        )

    async def publish_room_character_updated(
        self,
        *,
        room_id: int,
        entry: dict[str, Any],
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.ROOM_CHARACTER_UPDATED,
            data={"room_id": room_id, "entry": entry},
        )

    async def publish_character_state_updated(
        self,
        *,
        room_id: int,
        character_id: int,
        state_summary: dict[str, Any],
        state_summary_public: dict[str, Any] | None = None,
    ) -> None:
        data: dict[str, Any] = {
            "room_id": room_id,
            "character_id": character_id,
            "state_summary": state_summary,
        }
        if state_summary_public is not None:
            data["state_summary_public"] = state_summary_public
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.CHARACTER_STATE_UPDATED,
            data=data,
        )

    async def publish_pointer_presence(
        self,
        *,
        room_id: int,
        user_id: int,
        display_name: str,
        x: float,
        y: float,
        exclude_connection_ids: set[str] | None = None,
    ) -> None:
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.POINTER_PRESENCE,
            data={
                "room_id": room_id,
                "user_id": user_id,
                "display_name": display_name,
                "x": x,
                "y": y,
            },
            exclude_connection_ids=exclude_connection_ids,
        )

    async def publish_pointer_laser(
        self,
        *,
        room_id: int,
        user_id: int,
        display_name: str,
        active: bool,
        x1: float,
        y1: float,
        x2: float | None = None,
        y2: float | None = None,
    ) -> None:
        data: dict[str, Any] = {
            "room_id": room_id,
            "user_id": user_id,
            "display_name": display_name,
            "active": active,
            "x1": x1,
            "y1": y1,
        }
        if x2 is not None:
            data["x2"] = x2
        if y2 is not None:
            data["y2"] = y2
        await self._publish_event(
            channel=room_channel(room_id),
            event=WsEventType.POINTER_LASER,
            data=data,
        )

    async def publish_room_user_presence(
        self,
        *,
        presence: PresenceState,
        exclude_connection_ids: set[str] | None = None,
    ) -> None:
        await self._publish_event(
            channel=room_channel(presence.room_id),
            event=WsEventType.ROOM_USER_PRESENCE,
            data=presence.model_dump(mode="json"),
            exclude_connection_ids=exclude_connection_ids,
        )

    async def publish_session_closed(
        self,
        *,
        connection_id: str,
        room_id: int,
        reason: SessionCloseReason,
    ) -> None:
        await self.manager.send_to_connection(
            connection_id=connection_id,
            message=build_event_message(
                event=WsEventType.SESSION_CLOSED,
                data={
                    "room_id": room_id,
                    "reason": reason,
                },
            ),
        )

