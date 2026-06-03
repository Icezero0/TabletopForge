from app.modules.site.constants import SiteRole


async def test_user_can_upload_and_read_own_avatar(
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

    content_response = await api_client.get(
        body["avatar_url"],
        headers=auth_headers(user),
    )

    assert content_response.status_code == 200
    assert content_response.content == sample_upload_bytes
    assert content_response.headers["content-type"].startswith("image/png")


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
