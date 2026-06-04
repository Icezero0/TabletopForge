from app.modules.rooms.models import RoomPersonalMemo


async def test_get_personal_memo_returns_empty_for_member_without_row(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.get(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200
    assert response.json()["content"] == ""
    assert response.json()["updated_at"] is None


async def test_put_and_get_personal_memo_persists_for_member(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member)
    await factories.commit()

    put_response = await api_client.put(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(member),
        json={"content": "my private notes"},
    )
    assert put_response.status_code == 200
    assert put_response.json()["content"] == "my private notes"
    assert put_response.json()["updated_at"] is not None

    get_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(member),
    )
    assert get_response.status_code == 200
    assert get_response.json()["content"] == "my private notes"

    memos = await factories.list_all(RoomPersonalMemo)
    assert len(memos) == 1
    assert memos[0].user_id == member.id
    assert memos[0].room_id == room.id


async def test_personal_memo_isolated_per_user(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member)
    await factories.commit()

    await api_client.put(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(owner),
        json={"content": "owner notes"},
    )
    await api_client.put(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(member),
        json={"content": "member notes"},
    )

    owner_get = await api_client.get(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(owner),
    )
    member_get = await api_client.get(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(member),
    )

    assert owner_get.json()["content"] == "owner notes"
    assert member_get.json()["content"] == "member notes"


async def test_personal_memo_rejects_non_member(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    outsider = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.get(
        f"/api/v1/rooms/{room.id}/personal-memo",
        headers=auth_headers(outsider),
    )

    assert response.status_code == 403
