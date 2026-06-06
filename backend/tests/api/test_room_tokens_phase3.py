from unittest.mock import AsyncMock

from app.modules.rooms.constants import GameRole


async def test_spawn_token_links_character_and_includes_state_summary(
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
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={
            "kind": "pc",
            "name": "战士",
            "state_json": '{"max_hp": 20, "current_hp": 18, "armor_class": 16}',
            "attributes_json": (
                '{"derived": {"passive_perception": {"value": 14}}}'
            ),
        },
    )
    character_id = create_response.json()["character_id"]

    publish_token_created = AsyncMock()
    app.state.realtime_publisher.publish_token_created = publish_token_created

    spawn_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl),
        json={"x": 100, "y": 200},
    )

    assert spawn_response.status_code == 201
    body = spawn_response.json()
    assert body["linked_character_id"] == character_id
    assert body["linked_character_owner_id"] == pl.id
    assert body["name"] == "战士"
    assert body["x"] == 100
    assert body["y"] == 200
    assert body["width"] == 5.0
    assert body["height"] == 5.0
    summary = body["state_summary"]
    assert summary["current_hp"] == 18
    assert summary["max_hp"] == 20
    assert summary["ac"] == 16
    assert summary["pp"] == 14
    publish_token_created.assert_awaited_once()


async def test_same_character_can_spawn_multiple_tokens(
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
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={"kind": "pc", "name": "Dup"},
    )
    character_id = create_response.json()["character_id"]

    first = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl),
        json={"x": 0, "y": 0},
    )
    second = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl),
        json={"x": 10, "y": 10, "name": "Dup #2"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert second.json()["name"] == "Dup #2"


async def test_spawn_token_rejects_character_not_in_room(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    other_room = await factories.create_room(owner=owner)
    await factories.commit()
    other_character = await api_client.post(
        f"/api/v1/rooms/{other_room.id}/characters",
        headers=auth_headers(owner),
        data={"kind": "pc", "name": "Elsewhere"},
    )
    character_id = other_character.json()["character_id"]

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl),
        json={},
    )
    assert response.status_code == 400


async def test_pl_cannot_spawn_other_players_character(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl_a = await factories.create_user()
    pl_b = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl_a, game_role=GameRole.PL)
    await factories.add_member(room=room, user=pl_b, game_role=GameRole.PL)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl_b),
        data={"kind": "pc", "name": "B Hero"},
    )
    character_id = create_response.json()["character_id"]

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl_a),
        json={},
    )
    assert response.status_code == 403


async def test_gm_spawned_token_can_be_patched_by_pl_owner(
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
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={"kind": "pc", "name": "PL Hero"},
    )
    character_id = create_response.json()["character_id"]

    spawn_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(owner),
        json={"x": 0, "y": 0},
    )
    token_id = spawn_response.json()["id"]
    assert spawn_response.json()["owner_user_id"] == owner.id

    app.state.realtime_publisher.publish_token_updated = AsyncMock()

    patch_response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(pl),
        json={"x": 42},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["x"] == 42


async def test_pl_cannot_patch_bound_token_for_other_character(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl_a = await factories.create_user()
    pl_b = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl_a, game_role=GameRole.PL)
    await factories.add_member(room=room, user=pl_b, game_role=GameRole.PL)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl_b),
        data={"kind": "pc", "name": "B"},
    )
    character_id = create_response.json()["character_id"]

    spawn_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl_b),
        json={},
    )
    token_id = spawn_response.json()["id"]

    patch_response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(pl_a),
        json={"x": 99},
    )
    assert patch_response.status_code == 403


async def test_snapshot_includes_state_summary_on_linked_tokens(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(owner),
        data={
            "kind": "pc",
            "name": "Snap",
            "state_json": '{"max_hp": 10, "current_hp": 8, "armor_class": 12}',
        },
    )
    character_id = create_response.json()["character_id"]

    await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(owner),
        json={},
    )

    snapshot = await api_client.get(
        f"/api/v1/rooms/{room.id}/tabletop",
        headers=auth_headers(owner),
    )
    assert snapshot.status_code == 200
    tokens = snapshot.json()["tokens"]
    assert len(tokens) == 1
    assert tokens[0]["state_summary"]["current_hp"] == 8
    assert tokens[0]["state_summary"]["max_hp"] == 10
    assert tokens[0]["state_summary"]["ac"] == 12


async def test_create_token_rejects_invalid_linked_character(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/tokens",
        headers=auth_headers(owner),
        data={"name": "Bad Link", "x": "0", "y": "0", "linked_character_id": "99999"},
    )
    assert response.status_code == 400


async def test_state_patch_broadcasts_character_state_updated(
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
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={
            "kind": "pc",
            "name": "WS Hero",
            "state_json": '{"max_hp": 20, "current_hp": 20, "armor_class": 15}',
        },
    )
    character_id = create_response.json()["character_id"]

    publish_state_updated = AsyncMock()
    app.state.realtime_publisher.publish_character_state_updated = publish_state_updated

    patch_response = await api_client.patch(
        f"/api/v1/characters/{character_id}/state",
        headers=auth_headers(pl),
        json={"current_hp": 11, "armor_class": 17},
    )
    assert patch_response.status_code == 200

    publish_state_updated.assert_awaited_once()
    call_kwargs = publish_state_updated.await_args.kwargs
    assert call_kwargs["room_id"] == room.id
    assert call_kwargs["character_id"] == character_id
    assert call_kwargs["state_summary"]["current_hp"] == 11
    assert call_kwargs["state_summary"]["ac"] == 17

    spawn_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl),
        json={},
    )
    token_id = spawn_response.json()["id"]

    patch_token_response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tokens/{token_id}",
        headers=auth_headers(pl),
        json={"y": 5},
    )
    assert patch_token_response.json()["state_summary"]["current_hp"] == 11
