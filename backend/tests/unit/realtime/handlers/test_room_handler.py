from types import SimpleNamespace

import pytest

from app.core.exceptions import BadRequestError, ForbiddenError
from app.realtime.constants import WsCommandAction
from app.realtime.handlers.room import RoomCommandHandler
from app.realtime.manager import WsConnection
from app.realtime.room_presence import RoomPresenceService
from app.realtime.state import PresenceState


class RecordingPublisher:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def publish_room_user_presence(self, **kwargs) -> None:
        self.calls.append(("publish_room_user_presence", kwargs))

    async def publish_session_closed(self, **kwargs) -> None:
        self.calls.append(("publish_session_closed", kwargs))


def make_connection(*, user_id: int = 1, active_room_id: int | None = None) -> WsConnection:
    return WsConnection(
        connection_id="conn-1",
        user_id=user_id,
        websocket=SimpleNamespace(),
        active_room_id=active_room_id,
    )


async def test_handle_room_presence_get_returns_presence(monkeypatch) -> None:
    presence_service = RoomPresenceService()
    handler = RoomCommandHandler(presence_service=presence_service)
    connection = make_connection(active_room_id=10)

    async def fake_get_presence_state(*, room_id):  # noqa: ANN001
        assert room_id == 10
        return PresenceState(room_id=10, present_user_ids=[1, 2])

    monkeypatch.setattr(presence_service, "get_presence_state", fake_get_presence_state)

    result = await handler.handle(
        db=SimpleNamespace(),
        manager=SimpleNamespace(),
        publisher=RecordingPublisher(),
        connection=connection,
        command=SimpleNamespace(action=WsCommandAction.ROOM_PRESENCE_GET, data=None),
    )

    assert result == {
        "presence": {"room_id": 10, "present_user_ids": [1, 2]},
    }


def test_require_active_room_rejects_connection_without_room() -> None:
    with pytest.raises(BadRequestError) as exc_info:
        RoomCommandHandler._require_active_room(make_connection(active_room_id=None))

    assert exc_info.value.message == "You must enter a room before querying room state"


async def test_handle_room_enter_returns_presence_snapshot(monkeypatch) -> None:
    presence_service = RoomPresenceService()
    handler = RoomCommandHandler(presence_service=presence_service)
    publisher = RecordingPublisher()
    connection = make_connection(user_id=7)
    current_presence = PresenceState(room_id=20, present_user_ids=[7])

    async def fake_get_room_by_id(db, room_id):  # noqa: ANN001
        assert room_id == 20
        return SimpleNamespace(id=room_id)

    async def fake_find_room_role(db, room_id, user_id):  # noqa: ANN001
        assert (room_id, user_id) == (20, 7)
        return "member"

    async def fake_find_room_user_connection(*, room_id, user_id):  # noqa: ANN001
        return None

    async def fake_enter_room(**kwargs):  # noqa: ANN001
        kwargs["connection"].active_room_id = kwargs["room_id"]
        return current_presence

    monkeypatch.setattr(handler.room_service, "get_room_by_id", fake_get_room_by_id)
    monkeypatch.setattr(handler.membership_service, "find_room_role", fake_find_room_role)
    monkeypatch.setattr(presence_service, "find_room_user_connection", fake_find_room_user_connection)
    monkeypatch.setattr(presence_service, "enter_room", fake_enter_room)

    result = await handler.handle(
        db=SimpleNamespace(),
        manager=SimpleNamespace(),
        publisher=publisher,
        connection=connection,
        command=SimpleNamespace(
            action=WsCommandAction.ROOM_ENTER,
            data={"room_id": 20},
        ),
    )

    assert result == {"room_id": 20, "present_user_ids": [7]}
    assert publisher.calls == [
        (
            "publish_room_user_presence",
            {
                "presence": current_presence,
                "exclude_connection_ids": {"conn-1"},
            },
        )
    ]


async def test_handle_room_enter_rejects_non_member(monkeypatch) -> None:
    presence_service = RoomPresenceService()
    handler = RoomCommandHandler(presence_service=presence_service)

    async def fake_get_room_by_id(db, room_id):  # noqa: ANN001
        return SimpleNamespace(id=room_id)

    async def fake_find_room_role(db, room_id, user_id):  # noqa: ANN001
        return None

    monkeypatch.setattr(handler.room_service, "get_room_by_id", fake_get_room_by_id)
    monkeypatch.setattr(handler.membership_service, "find_room_role", fake_find_room_role)

    with pytest.raises(ForbiddenError):
        await handler.handle(
            db=SimpleNamespace(),
            manager=SimpleNamespace(),
            publisher=RecordingPublisher(),
            connection=make_connection(user_id=7),
            command=SimpleNamespace(
                action=WsCommandAction.ROOM_ENTER,
                data={"room_id": 20},
            ),
        )


async def test_handle_room_leave_publishes_presence(monkeypatch) -> None:
    presence_service = RoomPresenceService()
    handler = RoomCommandHandler(presence_service=presence_service)
    publisher = RecordingPublisher()
    presence = PresenceState(room_id=30, present_user_ids=[])

    async def fake_leave_room(**kwargs):  # noqa: ANN001
        return True

    async def fake_get_presence_state(*, room_id):  # noqa: ANN001
        assert room_id == 30
        return presence

    monkeypatch.setattr(presence_service, "leave_room", fake_leave_room)
    monkeypatch.setattr(presence_service, "get_presence_state", fake_get_presence_state)

    result = await handler.handle(
        db=SimpleNamespace(),
        manager=SimpleNamespace(),
        publisher=publisher,
        connection=make_connection(user_id=7, active_room_id=30),
        command=SimpleNamespace(
            action=WsCommandAction.ROOM_LEAVE,
            data={"room_id": 30},
        ),
    )

    assert result is None
    assert publisher.calls == [
        (
            "publish_room_user_presence",
            {
                "presence": presence,
                "exclude_connection_ids": {"conn-1"},
            },
        )
    ]
