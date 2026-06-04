from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.rooms.constants import GameRole
from app.realtime.constants import WsCommandAction
from app.realtime.handlers.tabletop import TabletopCommandHandler
from app.realtime.manager import WsConnection
from app.realtime.protocol import WsCommandPayload


@pytest.mark.asyncio
async def test_pointer_presence_publishes_event(monkeypatch) -> None:
    handler = TabletopCommandHandler()
    connection = WsConnection(
        connection_id="conn-1",
        user_id=9,
        websocket=SimpleNamespace(),
        active_room_id=42,
    )
    publisher = SimpleNamespace(publish_pointer_presence=AsyncMock())

    async def fake_game_role(*_args, **_kwargs):
        return GameRole.PL

    monkeypatch.setattr(handler.membership_service, "find_game_role", fake_game_role)
    monkeypatch.setattr(
        handler.user_repo,
        "get_by_id",
        AsyncMock(return_value=SimpleNamespace(username="Alice", email=None)),
    )

    command = WsCommandPayload(
        request_id="req-1",
        action=WsCommandAction.POINTER_PRESENCE,
        data={"room_id": 42, "x": 10.5, "y": 20.25},
    )

    await handler.handle(
        db=object(),
        manager=object(),
        publisher=publisher,
        connection=connection,
        command=command,
    )

    publisher.publish_pointer_presence.assert_awaited_once()
    kwargs = publisher.publish_pointer_presence.await_args.kwargs
    assert kwargs["room_id"] == 42
    assert kwargs["user_id"] == 9
    assert kwargs["display_name"] == "Alice"
    assert kwargs["x"] == 10.5
    assert kwargs["y"] == 20.25


@pytest.mark.asyncio
async def test_pointer_laser_publishes_event(monkeypatch) -> None:
    handler = TabletopCommandHandler()
    connection = WsConnection(
        connection_id="conn-2",
        user_id=3,
        websocket=SimpleNamespace(),
        active_room_id=7,
    )
    publisher = SimpleNamespace(publish_pointer_laser=AsyncMock())

    async def fake_game_role(*_args, **_kwargs):
        return GameRole.GM

    monkeypatch.setattr(handler.membership_service, "find_game_role", fake_game_role)
    monkeypatch.setattr(
        handler.user_repo,
        "get_by_id",
        AsyncMock(return_value=SimpleNamespace(username=None, email="gm@test")),
    )

    command = WsCommandPayload(
        request_id="req-2",
        action=WsCommandAction.POINTER_LASER,
        data={"room_id": 7, "active": True, "x1": 1, "y1": 2, "x2": 3, "y2": 4},
    )

    await handler.handle(
        db=object(),
        manager=object(),
        publisher=publisher,
        connection=connection,
        command=command,
    )

    publisher.publish_pointer_laser.assert_awaited_once()
    kwargs = publisher.publish_pointer_laser.await_args.kwargs
    assert kwargs["active"] is True
    assert kwargs["x2"] == 3
    assert kwargs["y2"] == 4
