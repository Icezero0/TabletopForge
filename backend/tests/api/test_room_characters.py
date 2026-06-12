from app.modules.rooms.constants import GameRole


async def _create_global_character_via_api(api_client, auth_headers, user, *, name: str):
    response = await api_client.post(
        "/api/v1/characters",
        headers=auth_headers(user),
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_pl_can_create_multiple_characters_in_room(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    pc_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={
            "name": "主 PC",
            "player_name": "玩家A",
            "state_json": '{"max_hp": 30, "current_hp": 30, "armor_class": 16}',
        },
    )
    assert pc_response.status_code == 201
    pc_body = pc_response.json()
    assert pc_body["name"] == "主 PC"
    assert pc_body["player_name"] == "玩家A"
    assert pc_body["state"]["max_hp"] == 30
    assert pc_body["state"]["armor_class"] == 16

    add_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={
            "name": "酒馆老板",
            "flavor_json": '{"backstory": "认识所有人"}',
        },
    )
    assert add_response.status_code == 201
    assert add_response.json()["name"] == "酒馆老板"

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
    )
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 2
    names = {item["name"] for item in items}
    assert names == {"主 PC", "酒馆老板"}


async def test_quick_room_character_without_image_gets_primary_token_config_and_can_spawn(
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
            "name": "无头像角色",
            "state_json": '{"max_hp": 18, "current_hp": 18, "armor_class": 13}',
        },
    )

    assert create_response.status_code == 201
    body = create_response.json()
    configs = body["token_configs"]
    assert len(configs) == 1
    assert configs[0]["is_primary"] is True
    assert configs[0]["name"] == "无头像角色"
    assert configs[0]["asset_id"] is None

    spawn_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{body['character_id']}/spawn-token",
        headers=auth_headers(pl),
        json={"x": 12, "y": 34},
    )
    assert spawn_response.status_code == 201
    token = spawn_response.json()
    assert token["name"] == "无头像角色"
    assert token["asset_id"] is None
    assert token["panel"]["hp_current"] == 18
    assert token["panel"]["hp_max"] == 18
    assert token["panel"]["ac"] == 13


async def test_ob_can_list_but_not_create_room_character(
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
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(ob),
        data={"name": "Blocked"},
    )
    assert create_response.status_code == 403

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(ob),
    )
    assert list_response.status_code == 200
    assert list_response.json() == []


async def test_pl_can_patch_own_state_but_not_others(
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

    create_a = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl_a),
        data={"name": "A"},
    )
    create_b = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl_b),
        data={"name": "B"},
    )
    char_a_id = create_a.json()["character_id"]
    char_b_id = create_b.json()["character_id"]

    own_patch = await api_client.patch(
        f"/api/v1/characters/{char_a_id}/state",
        headers=auth_headers(pl_a),
        json={"current_hp": 12, "armor_class": 15},
    )
    assert own_patch.status_code == 200
    assert own_patch.json()["current_hp"] == 12
    assert own_patch.json()["armor_class"] == 15

    other_patch = await api_client.patch(
        f"/api/v1/characters/{char_b_id}/state",
        headers=auth_headers(pl_a),
        json={"current_hp": 1},
    )
    assert other_patch.status_code == 403


async def test_gm_can_patch_pl_character_state(
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
        data={"name": "PL Hero"},
    )
    character_id = create_response.json()["character_id"]

    patch_response = await api_client.patch(
        f"/api/v1/characters/{character_id}/state",
        headers=auth_headers(owner),
        json={"current_hp": 5},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["current_hp"] == 5

    get_response = await api_client.get(
        f"/api/v1/characters/{character_id}/state",
        headers=auth_headers(owner),
    )
    assert get_response.status_code == 200
    assert get_response.json()["current_hp"] == 5


async def test_room_member_can_get_character_in_room(
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
        data={"name": "PL Hero"},
    )
    character_id = create_response.json()["character_id"]

    gm_get = await api_client.get(
        f"/api/v1/characters/{character_id}",
        headers=auth_headers(owner),
    )
    assert gm_get.status_code == 200
    assert gm_get.json()["name"] == "PL Hero"

    pl_get = await api_client.get(
        f"/api/v1/characters/{character_id}",
        headers=auth_headers(pl),
    )
    assert pl_get.status_code == 200
    assert pl_get.json()["name"] == "PL Hero"


async def test_token_image_upload_and_readable_by_room_member(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={"name": "Token Hero"},
        files={"file": ("token.png", sample_upload_bytes, "image/png")},
    )
    assert create_response.status_code == 201
    asset_id = create_response.json()["token_image_asset_id"]
    assert asset_id is not None

    asset_response = await api_client.get(
        f"/api/v1/assets/{asset_id}/content",
        headers=auth_headers(owner),
    )
    assert asset_response.status_code == 200

    outsider = await factories.create_user()
    await factories.commit()
    denied = await api_client.get(
        f"/api/v1/assets/{asset_id}/content",
        headers=auth_headers(outsider),
    )
    assert denied.status_code == 403


async def test_pl_links_own_global_character_to_room(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    character_id = await _create_global_character_via_api(
        api_client, auth_headers, pl, name="Library Hero"
    )

    link_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/link",
        headers=auth_headers(pl),
        json={"character_id": character_id},
    )
    assert link_response.status_code == 200
    body = link_response.json()
    assert body["character_id"] == character_id
    assert body["name"] == "Library Hero"

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
    )
    assert len(list_response.json()) == 1


async def test_pl_cannot_link_other_players_character(
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

    character_id = await _create_global_character_via_api(
        api_client, auth_headers, pl_b, name="B Hero"
    )

    link_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/link",
        headers=auth_headers(pl_a),
        json={"character_id": character_id},
    )
    assert link_response.status_code == 403


async def test_gm_links_own_global_character_to_room(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    character_id = await _create_global_character_via_api(
        api_client, auth_headers, owner, name="GM Character"
    )

    link_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/link",
        headers=auth_headers(owner),
        json={"character_id": character_id},
    )
    assert link_response.status_code == 200
    assert link_response.json()["name"] == "GM Character"


async def test_link_room_character_is_idempotent(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    character_id = await _create_global_character_via_api(
        api_client, auth_headers, pl, name="Dup Link"
    )

    first = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/link",
        headers=auth_headers(pl),
        json={"character_id": character_id},
    )
    second = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/link",
        headers=auth_headers(pl),
        json={"character_id": character_id},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["room_character_id"] == second.json()["room_character_id"]


async def test_link_then_spawn_token(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    character_id = await _create_global_character_via_api(
        api_client, auth_headers, pl, name="Spawn Me"
    )

    link_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/link",
        headers=auth_headers(pl),
        json={"character_id": character_id},
    )
    assert link_response.status_code == 200

    spawn_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters/{character_id}/spawn-token",
        headers=auth_headers(pl),
        json={"x": 0, "y": 0},
    )
    assert spawn_response.status_code == 201
