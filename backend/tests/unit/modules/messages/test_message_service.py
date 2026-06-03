import json

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.messages.schemas import MessageContentIn, MessageCreate
from app.modules.messages.service import MessageService


async def test_create_message_persists_text_content(db_session, factories) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    payload = MessageCreate(
        content=MessageContentIn.model_validate(
            {"segments": [{"type": "text", "text": "hello"}]}
        )
    )

    message = await MessageService().create_message(
        db_session,
        room_id=room.id,
        user=owner,
        payload=payload,
    )

    assert message.sender_user_id == owner.id
    assert [segment.type for segment in message.content.segments] == ["text"]
    assert message.content.segments[0].text == "hello"


async def test_create_message_rejects_user_without_room_access(db_session, factories) -> None:
    owner = await factories.create_user()
    outsider = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    with pytest.raises(ForbiddenError, match="You do not have permission"):
        await MessageService().create_message(
            db_session,
            room_id=room.id,
            user=outsider,
            payload=MessageCreate.model_validate(
                {"content": {"segments": [{"type": "text", "text": "hello"}]}}
            ),
        )


async def test_get_messages_returns_oldest_first_and_sets_next_before_id(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    first = await factories.create_message(
        room=room,
        sender=owner,
        content=json.dumps({"segments": [{"type": "text", "text": "1"}]}),
    )
    second = await factories.create_message(
        room=room,
        sender=owner,
        content=json.dumps({"segments": [{"type": "text", "text": "2"}]}),
    )
    third = await factories.create_message(
        room=room,
        sender=owner,
        content=json.dumps({"segments": [{"type": "text", "text": "3"}]}),
    )
    await factories.commit()

    data = await MessageService().get_messages(
        db_session,
        room_id=room.id,
        user=owner,
        limit=2,
    )

    assert first.id < second.id < third.id
    assert [item.id for item in data.items] == [second.id, third.id]
    assert data.next_before_id == second.id
