from app.modules.rooms.constants import GameRole


async def test_pl_can_create_pc_and_additional_in_room(
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
            "kind": "pc_main",
            "name": "主 PC",
            "player_name": "玩家A",
            "state_json": '{"max_hp": 30, "current_hp": 30, "armor_class": 16}',
        },
    )
    assert pc_response.status_code == 201
    pc_body = pc_response.json()
    assert pc_body["kind"] == "pc_main"
    assert pc_body["name"] == "主 PC"
    assert pc_body["player_name"] == "玩家A"
    assert pc_body["state"]["max_hp"] == 30
    assert pc_body["state"]["armor_class"] == 16

    add_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={
            "kind": "pc_additional",
            "name": "酒馆老板",
            "flavor_json": '{"backstory": "认识所有人"}',
        },
    )
    assert add_response.status_code == 201
    assert add_response.json()["kind"] == "pc_additional"

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
    )
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 2
    kinds = {item["kind"] for item in items}
    assert kinds == {"pc_main", "pc_additional"}


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
        data={"kind": "pc_main", "name": "Blocked"},
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
        data={"kind": "pc_main", "name": "A"},
    )
    create_b = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl_b),
        data={"kind": "pc_main", "name": "B"},
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
        data={"kind": "pc_main", "name": "PL Hero"},
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
        data={"kind": "pc_main", "name": "PL Hero"},
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
        data={"kind": "pc_main", "name": "Token Hero"},
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


async def test_pl_cannot_create_npc_in_room(
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
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
        data={"kind": "npc", "name": "Blocked NPC"},
    )
    assert response.status_code == 400


async def test_gm_cannot_create_pc_main_in_room(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(owner),
        data={"kind": "pc_main", "name": "Blocked PC"},
    )
    assert response.status_code == 400
