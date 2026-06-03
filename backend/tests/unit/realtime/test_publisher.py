from datetime import UTC, datetime

from app.modules.messages.schemas import MessageContentOut, MessageResponse, TextSegmentOut
from app.realtime.constants import WsEventType
from app.realtime.publisher import RealtimePublisher
from app.realtime.state import PresenceState


class RecordingManager:
    def __init__(self) -> None:
        self.publish_calls: list[dict] = []
        self.send_calls: list[dict] = []

    async def publish(self, **kwargs) -> None:
        self.publish_calls.append(kwargs)

    async def send_to_connection(self, **kwargs) -> None:
        self.send_calls.append(kwargs)


# publish_room_user_presence 会把 presence 状态封装成房间事件并广播到房间频道
async def test_publish_presence_broadcasts_presence_event() -> None:
    manager = RecordingManager()
    publisher = RealtimePublisher(manager)
    presence = PresenceState(room_id=8, present_user_ids=[1, 2])

    await publisher.publish_room_user_presence(
        presence=presence,
        exclude_connection_ids={"conn-1"},
    )

    assert len(manager.publish_calls) == 1
    call = manager.publish_calls[0]
    assert call["channel"].target_id == "8"
    assert call["exclude_connection_ids"] == {"conn-1"}
    assert call["message"].payload["event"] == WsEventType.ROOM_USER_PRESENCE
    assert call["message"].payload["data"] == {"room_id": 8, "present_user_ids": [1, 2]}


# publish_session_closed 会向指定连接单播会话关闭事件
async def test_publish_session_sends_session_event_to_single_connection() -> None:
    manager = RecordingManager()
    publisher = RealtimePublisher(manager)

    await publisher.publish_session_closed(
        connection_id="conn-2",
        room_id=9,
        reason="entered_elsewhere",
    )

    assert len(manager.send_calls) == 1
    call = manager.send_calls[0]
    assert call["connection_id"] == "conn-2"
    assert call["message"].payload["event"] == WsEventType.SESSION_CLOSED
    assert call["message"].payload["data"] == {"room_id": 9, "reason": "entered_elsewhere"}


# publish_message 会把消息响应作为聊天事件广播到房间频道
async def test_publish_message_broadcasts_message_event() -> None:
    manager = RecordingManager()
    publisher = RealtimePublisher(manager)
    message = MessageResponse(
        id=1,
        room_id=10,
        sender_user_id=20,
        sender=None,
        content=MessageContentOut(segments=[TextSegmentOut(type="text", text="hello")]),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    await publisher.publish_message(room_id=10, message=message)

    assert len(manager.publish_calls) == 1
    call = manager.publish_calls[0]
    assert call["message"].payload["event"] == WsEventType.MESSAGE
    assert call["message"].payload["data"]["id"] == 1

