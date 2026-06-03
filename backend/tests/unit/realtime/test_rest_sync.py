from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.realtime.rest_sync import close_room_sessions, close_room_user_session


# 验证关闭房间用户会话时，如果没有活动连接则不会执行后续动作。
async def test_close_room_user_session_returns_false_when_connection_missing(
    db_session,
) -> None:
    presence_service = SimpleNamespace(
        find_room_user_connection=AsyncMock(return_value=None),
    )

    result = await close_room_user_session(
        manager=SimpleNamespace(),
        publisher=SimpleNamespace(),
        presence_service=presence_service,
        room_id=1,
        user_id=2,
        reason="removed",
    )

    assert result is False


# 验证关闭房间用户会话时会发布会话关闭和在线状态更新。
async def test_close_room_user_session_publishes_presence_update() -> None:
    publisher = SimpleNamespace(
        publish_session_closed=AsyncMock(),
        publish_room_user_presence=AsyncMock(),
    )
    presence = SimpleNamespace(room_id=1, present_user_ids={10})
    presence_service = SimpleNamespace(
        find_room_user_connection=AsyncMock(return_value="conn-1"),
        evict_room_user=AsyncMock(return_value="conn-1"),
        get_presence_state=AsyncMock(return_value=presence),
    )

    result = await close_room_user_session(
        manager=SimpleNamespace(),
        publisher=publisher,
        presence_service=presence_service,
        room_id=1,
        user_id=10,
        reason="removed",
    )

    assert result is True
    publisher.publish_session_closed.assert_awaited_once()
    publisher.publish_room_user_presence.assert_awaited_once_with(presence=presence)


# 验证关闭房间全部会话时，如果没有活动连接则直接返回空列表。
async def test_close_room_sessions_returns_empty_list_without_connections() -> None:
    closed_user_ids = await close_room_sessions(
        manager=SimpleNamespace(),
        publisher=SimpleNamespace(publish_session_closed=AsyncMock()),
        presence_service=SimpleNamespace(evict_room_users=AsyncMock(return_value=[])),
        room_id=1,
        reason="room_deleted",
    )

    assert closed_user_ids == []
