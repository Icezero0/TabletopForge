from app.modules.rooms.constants import GameRole


async def _create_gm_npc(api_client, room_id, gm, auth_headers):
    return await api_client.post(
        f"/api/v1/rooms/{room_id}/characters",
        headers=auth_headers(gm),
        data={
            "kind": "additional",
            "name": "Goblin",
            "state_json": '{"max_hp": 7, "current_hp": 7, "armor_class": 15}',
        },
    )


async def test_pl_list_gm_npc_hides_exact_hp(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    create_response = await _create_gm_npc(api_client, room.id, owner, auth_headers)
    assert create_response.status_code == 201
    character_id = create_response.json()["character_id"]

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(pl),
    )
    assert list_response.status_code == 200
    entry = next(i for i in list_response.json() if i["character_id"] == character_id)
    assert entry["state"]["damage_taken"] == 0
    assert entry["state"]["current_hp"] is None
    assert entry["state"]["max_hp"] is None
    assert entry["state"]["armor_class"] is None


async def test_gm_list_own_npc_shows_full_hp(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    create_response = await _create_gm_npc(api_client, room.id, owner, auth_headers)
    assert create_response.status_code == 201
    character_id = create_response.json()["character_id"]

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(owner),
    )
    entry = next(i for i in list_response.json() if i["character_id"] == character_id)
    assert entry["state"]["current_hp"] == 7
    assert entry["state"]["max_hp"] == 7
    assert entry["state"]["armor_class"] == 15


async def test_pl_get_gm_npc_state_damage_only(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    create_response = await _create_gm_npc(api_client, room.id, owner, auth_headers)
    character_id = create_response.json()["character_id"]

    await api_client.patch(
        f"/api/v1/characters/{character_id}/state",
        headers=auth_headers(owner),
        json={"current_hp": 2},
    )

    pl_state = await api_client.get(
        f"/api/v1/characters/{character_id}/state",
        headers=auth_headers(pl),
    )
    assert pl_state.status_code == 200
    body = pl_state.json()
    assert body["current_hp"] is None
    assert body["max_hp"] is None
    assert body["armor_class"] is None
    assert body["damage_taken"] == 5


async def test_gm_patch_hp_increments_damage_taken(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    create_response = await _create_gm_npc(api_client, room.id, owner, auth_headers)
    character_id = create_response.json()["character_id"]

    patch_response = await api_client.patch(
        f"/api/v1/characters/{character_id}/state",
        headers=auth_headers(owner),
        json={"current_hp": 4},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["damage_taken"] == 3
    assert patch_response.json()["current_hp"] == 4


async def test_portrait_falls_back_to_token_image(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    upload = await api_client.post(
        "/api/v1/assets",
        headers=auth_headers(owner),
        data={"asset_type": "image"},
        files={"file": ("portrait.png", sample_upload_bytes, "image/png")},
    )
    assert upload.status_code == 200
    portrait_id = upload.json()["id"]

    create_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/characters",
        headers=auth_headers(owner),
        data={
            "kind": "additional",
            "name": "NPC",
            "portrait_asset_id": str(portrait_id),
        },
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["token_image_asset_id"] == portrait_id
