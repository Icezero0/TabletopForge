from __future__ import annotations

from app.realtime.constants import SessionCloseReason
from app.realtime.manager import RealtimeManager
from app.realtime.publisher import RealtimePublisher
from app.realtime.room_presence import RoomPresenceService


async def close_room_user_session(
    *,
    manager: RealtimeManager,
    publisher: RealtimePublisher,
    presence_service: RoomPresenceService,
    room_id: int,
    user_id: int,
    reason: SessionCloseReason,
) -> bool:
    connection_id = await presence_service.find_room_user_connection(
        room_id=room_id,
        user_id=user_id,
    )
    if connection_id is None:
        return False

    await publisher.publish_session_closed(
        connection_id=connection_id,
        room_id=room_id,
        reason=reason,
    )

    evicted_connection_id = await presence_service.evict_room_user(
        manager=manager,
        room_id=room_id,
        user_id=user_id,
    )
    if evicted_connection_id is None:
        return False

    presence = await presence_service.get_presence_state(room_id=room_id)
    await publisher.publish_room_user_presence(
        presence=presence,
    )
    return True


async def close_room_sessions(
    *,
    manager: RealtimeManager,
    publisher: RealtimePublisher,
    presence_service: RoomPresenceService,
    room_id: int,
    reason: SessionCloseReason,
) -> list[int]:
    active_connections = await presence_service.evict_room_users(
        manager=manager,
        room_id=room_id,
    )
    if not active_connections:
        return []

    for _, connection_id in active_connections:
        await publisher.publish_session_closed(
            connection_id=connection_id,
            room_id=room_id,
            reason=reason,
        )

    return [user_id for user_id, _ in active_connections]
