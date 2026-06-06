from app.modules.rooms.constants import GameRole


async def test_get_tabletop_creates_default_settings(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.get(
        f"/api/v1/rooms/{room.id}/tabletop",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["settings"]["grid_cell_ft"] == 5.0
    assert body["settings"]["grid_cell_px"] == 40
    assert body["maps"] == []
    assert body["drawings"] == []
    assert body["tokens"] == []


async def test_gm_can_upload_map_pl_cannot(
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

    gm_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/maps",
        headers=auth_headers(owner),
        files={"file": ("map.png", sample_upload_bytes, "image/png")},
    )
    assert gm_response.status_code == 201
    assert gm_response.json()["asset_id"] is not None

    pl_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/maps",
        headers=auth_headers(pl),
        files={"file": ("map2.png", sample_upload_bytes, "image/png")},
    )
    assert pl_response.status_code == 403


async def test_gm_can_upload_multiple_maps(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    first = await api_client.post(
        f"/api/v1/rooms/{room.id}/maps",
        headers=auth_headers(owner),
        files={"file": ("map.png", sample_upload_bytes, "image/png")},
    )
    assert first.status_code == 201
    assert first.json()["z_index"] == 0

    second = await api_client.post(
        f"/api/v1/rooms/{room.id}/maps",
        headers=auth_headers(owner),
        files={"file": ("map2.png", sample_upload_bytes, "image/png")},
    )
    assert second.status_code == 201
    assert second.json()["z_index"] == 1


async def test_pl_can_create_drawing_ob_cannot(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    ob = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.add_member(room=room, user=ob, game_role=GameRole.OB)
    await factories.commit()

    pl_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/drawings",
        headers=auth_headers(pl),
        json={
            "kind": "line",
            "geometry": {"points": [[0, 0], [10, 10]]},
            "style": {"color": "#ff0000", "width": 2},
        },
    )
    assert pl_response.status_code == 201

    ob_response = await api_client.post(
        f"/api/v1/rooms/{room.id}/drawings",
        headers=auth_headers(ob),
        json={
            "kind": "line",
            "geometry": {"points": [[0, 0], [1, 1]]},
            "style": {},
        },
    )
    assert ob_response.status_code == 403


async def test_patch_settings_gm_only(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    pl = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=pl, game_role=GameRole.PL)
    await factories.commit()

    await api_client.get(
        f"/api/v1/rooms/{room.id}/tabletop",
        headers=auth_headers(owner),
    )

    gm_patch = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tabletop/settings",
        headers=auth_headers(owner),
        json={"grid_cell_ft": 10},
    )
    assert gm_patch.status_code == 200
    assert gm_patch.json()["grid_cell_ft"] == 10

    pl_patch = await api_client.patch(
        f"/api/v1/rooms/{room.id}/tabletop/settings",
        headers=auth_headers(pl),
        json={"grid_cell_px": 48},
    )
    assert pl_patch.status_code == 403


async def test_map_background_asset_readable_by_room_member(
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
        f"/api/v1/rooms/{room.id}/maps",
        headers=auth_headers(owner),
        files={"file": ("map.png", sample_upload_bytes, "image/png")},
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
