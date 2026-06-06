from unittest.mock import AsyncMock

from app.modules.rooms.constants import GameRole


async def test_gm_can_create_token_without_image(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    publish_token_created = AsyncMock()
    app.state.realtime_publisher.publish_token_created = publish_token_created

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "战士", "x": "10", "y": "20"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "战士"
    assert body["asset_id"] is None
    assert body["width"] == 5.0
    assert body["height"] == 5.0
    assert body["owner_user_id"] == owner.id
    assert body["z_index"] == 0
    publish_token_created.assert_awaited_once()


async def test_gm_can_create_token_with_image(
    app,
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "Hero", "x": "0", "y": "0"},
        files={"file": ("token.png", sample_upload_bytes, "image/png")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["asset_id"] is not None
    assert body["name"] == "Hero"


async def test_pl_can_create_own_token(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(pl),
        data={"name": "My PC", "x": "5", "y": "5"},
    )

    assert response.status_code == 201
    assert response.json()["owner_user_id"] == pl.id


async def test_ob_cannot_create_token(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    ob = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=ob, game_role=GameRole.OB)
    await factories.commit()

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(ob),
        data={"name": "Blocked", "x": "0", "y": "0"},
    )

    assert response.status_code == 403


async def test_pl_cannot_patch_gm_token(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "GM Token", "x": "0", "y": "0"},
    )
    token_id = create_response.json()["id"]

    patch_response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(pl),
        json={"x": 100},
    )
    assert patch_response.status_code == 403


async def test_pl_can_patch_own_token(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(pl),
        data={"name": "PL Token", "x": "0", "y": "0"},
    )
    token_id = create_response.json()["id"]

    publish_token_updated = AsyncMock()
    app.state.realtime_publisher.publish_token_updated = publish_token_updated

    patch_response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(pl),
        json={"x": 50, "y": 60, "width": 10, "height": 10},
    )
    assert patch_response.status_code == 200
    body = patch_response.json()
    assert body["x"] == 50
    assert body["y"] == 60
    assert body["width"] == 10
    assert body["height"] == 10
    publish_token_updated.assert_awaited_once()


async def test_gm_can_delete_token(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "Delete Me", "x": "0", "y": "0"},
    )
    token_id = create_response.json()["id"]

    publish_token_deleted = AsyncMock()
    app.state.realtime_publisher.publish_token_deleted = publish_token_deleted

    delete_response = await api_client.delete(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(owner),
    )
    assert delete_response.status_code == 204
    publish_token_deleted.assert_awaited_once_with(room_id=room.id, token_id=token_id)

    snapshot = await api_client.get(
        f"/api/v1/rooms/{room.id}/tabletop",
        headers=auth_headers(owner),
    )
    assert snapshot.json()["tokens"] == []


async def test_ob_cannot_delete_token(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    ob = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=ob, game_role=GameRole.OB)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "Read Only", "x": "0", "y": "0"},
    )
    token_id = create_response.json()["id"]

    delete_response = await api_client.delete(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(ob),
    )
    assert delete_response.status_code == 403


async def test_token_image_asset_readable_by_room_member(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    outsider = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, game_role=GameRole.PL)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "With Image", "x": "0", "y": "0"},
        files={"file": ("token.png", sample_upload_bytes, "image/png")},
    )
    asset_id = create_response.json()["asset_id"]

    member_content = await api_client.get(
        f"/api/v1/assets/{asset_id}/content",
        headers=auth_headers(member),
    )
    assert member_content.status_code == 200

    outsider_content = await api_client.get(
        f"/api/v1/assets/{asset_id}/content",
        headers=auth_headers(outsider),
    )
    assert outsider_content.status_code == 403
