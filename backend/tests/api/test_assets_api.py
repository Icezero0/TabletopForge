from app.modules.site.constants import SiteRole


async def test_user_can_upload_and_read_avatar_without_authorization_header(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    user = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["avatar_asset_id"] is not None
    assert body["avatar_url"] == f"/api/v1/assets/{body['avatar_asset_id']}/content"

    content_response = await api_client.get(body["avatar_url"])

    assert content_response.status_code == 200
    assert content_response.content == sample_upload_bytes
    assert content_response.headers["content-type"].startswith("image/png")


async def test_avatar_upload_records_history_and_reuses_same_file(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    user = await factories.create_user()
    await factories.commit()

    first_response = await api_client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("first.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(user),
    )
    second_response = await api_client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("second.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(user),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_avatar_id = first_response.json()["avatar_asset_id"]
    second_avatar_id = second_response.json()["avatar_asset_id"]
    assert second_avatar_id == first_avatar_id

    history_response = await api_client.get(
        "/api/v1/users/me/avatar-history",
        headers=auth_headers(user),
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["total"] == 2
    assert [item["asset_id"] for item in history["items"]] == [
        first_avatar_id,
        first_avatar_id,
    ]
    assert all(item["url"] == f"/api/v1/assets/{first_avatar_id}/content" for item in history["items"])

    asset_response = await api_client.get(f"/api/v1/assets/{first_avatar_id}")
    assert asset_response.status_code == 200
    assert asset_response.json()["ref_count"] == 2


async def test_feedback_image_access_follows_feedback_visibility(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    creator = await factories.create_user()
    admin = await factories.create_user(site_role=SiteRole.ADMIN)
    other_user = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/feedback",
        data={
            "feedback_type": "bug",
            "page": "room",
            "title": "Map did not load",
            "description": "The uploaded map stayed blank.",
        },
        files=[("images", ("screenshot.png", sample_upload_bytes, "image/png"))],
        headers=auth_headers(creator),
    )

    assert response.status_code == 200
    image = response.json()["images"][0]

    owner_response = await api_client.get(
        image["url"],
        headers=auth_headers(creator),
    )
    assert owner_response.status_code == 200
    assert owner_response.content == sample_upload_bytes

    admin_response = await api_client.get(
        image["url"],
        headers=auth_headers(admin),
    )
    assert admin_response.status_code == 200

    anonymous_response = await api_client.get(image["url"])
    assert anonymous_response.status_code == 401

    other_response = await api_client.get(
        image["url"],
        headers=auth_headers(other_user),
    )
    assert other_response.status_code == 403


async def test_rejects_non_image_asset_upload(
    api_client,
    factories,
    auth_headers,
) -> None:
    user = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["error"]["reason"] == "invalid_asset_file"


async def test_user_can_upload_list_read_and_delete_library_image(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    user = await factories.create_user()
    other_user = await factories.create_user()
    await factories.commit()

    upload_response = await api_client.post(
        "/api/v1/assets",
        data={"asset_type": "image"},
        files={"file": ("map.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(user),
    )

    assert upload_response.status_code == 200
    asset = upload_response.json()
    assert asset["asset_type"] == "image"
    assert asset["owner_id"] == user.id
    assert asset["content_hash"]
    assert asset["ref_count"] == 1
    assert asset["url"] == f"/api/v1/assets/{asset['id']}/content"

    list_response = await api_client.get(
        "/api/v1/assets",
        headers=auth_headers(user),
    )
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["total"] == 1
    assert list_body["items"][0]["id"] == asset["id"]

    content_response = await api_client.get(
        asset["url"],
        headers=auth_headers(user),
    )
    assert content_response.status_code == 200
    assert content_response.content == sample_upload_bytes
    assert content_response.headers["content-type"].startswith("image/png")

    anonymous_response = await api_client.get(asset["url"])
    assert anonymous_response.status_code == 200

    other_response = await api_client.get(
        asset["url"],
        headers=auth_headers(other_user),
    )
    assert other_response.status_code == 200

    delete_response = await api_client.delete(
        f"/api/v1/assets/{asset['id']}",
        headers=auth_headers(user),
    )
    assert delete_response.status_code == 204

    missing_response = await api_client.get(
        asset["url"],
        headers=auth_headers(user),
    )
    assert missing_response.status_code == 404


async def test_library_asset_upload_reuses_same_file_and_reference_count(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    first_user = await factories.create_user()
    second_user = await factories.create_user()
    await factories.commit()

    first_response = await api_client.post(
        "/api/v1/assets",
        data={"asset_type": "image"},
        files={"file": ("first.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(first_user),
    )
    second_response = await api_client.post(
        "/api/v1/assets",
        data={"asset_type": "image"},
        files={"file": ("second.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(second_user),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_asset = first_response.json()
    second_asset = second_response.json()
    assert second_asset["id"] == first_asset["id"]
    assert second_asset["content_hash"] == first_asset["content_hash"]
    assert second_asset["ref_count"] == 2

    first_release = await api_client.delete(
        f"/api/v1/assets/{first_asset['id']}",
        headers=auth_headers(first_user),
    )
    assert first_release.status_code == 204

    retained_response = await api_client.get(f"/api/v1/assets/{first_asset['id']}")
    assert retained_response.status_code == 200
    assert retained_response.json()["ref_count"] == 1

    second_release = await api_client.delete(
        f"/api/v1/assets/{first_asset['id']}",
        headers=auth_headers(second_user),
    )
    assert second_release.status_code == 204

    missing_response = await api_client.get(f"/api/v1/assets/{first_asset['id']}")
    assert missing_response.status_code == 404


async def test_user_can_upload_and_filter_library_audio(
    api_client,
    factories,
    auth_headers,
) -> None:
    user = await factories.create_user()
    await factories.commit()

    upload_response = await api_client.post(
        "/api/v1/assets",
        data={"asset_type": "audio"},
        files={"file": ("theme.mp3", b"fake-mp3", "audio/mpeg")},
        headers=auth_headers(user),
    )

    assert upload_response.status_code == 200
    asset = upload_response.json()
    assert asset["asset_type"] == "audio"
    assert asset["content_type"] == "audio/mpeg"

    image_list_response = await api_client.get(
        "/api/v1/assets",
        params={"asset_type": "image"},
        headers=auth_headers(user),
    )
    assert image_list_response.status_code == 200
    assert image_list_response.json()["total"] == 0

    audio_list_response = await api_client.get(
        "/api/v1/assets",
        params={"asset_type": "audio"},
        headers=auth_headers(user),
    )
    assert audio_list_response.status_code == 200
    assert audio_list_response.json()["items"][0]["id"] == asset["id"]


async def test_general_asset_upload_rejects_system_asset_type(
    api_client,
    factories,
    auth_headers,
    sample_upload_bytes,
) -> None:
    user = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/assets",
        data={"asset_type": "avatar"},
        files={"file": ("avatar.png", sample_upload_bytes, "image/png")},
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["error"]["reason"] == "invalid_asset_file"
