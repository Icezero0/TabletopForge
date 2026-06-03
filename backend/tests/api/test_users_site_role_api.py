from app.modules.site.constants import SitePermission, SiteRole


async def test_admin_can_promote_and_demote_another_user(
    api_client,
    factories,
    auth_headers,
) -> None:
    admin = await factories.create_user(site_role=SiteRole.ADMIN)
    user = await factories.create_user()
    await factories.commit()

    promote_response = await api_client.patch(
        f"/api/v1/users/{user.id}/site-role",
        json={"site_role": SiteRole.ADMIN.value},
        headers=auth_headers(admin),
    )

    assert promote_response.status_code == 200
    assert promote_response.json()["site_role"] == SiteRole.ADMIN.value

    demote_response = await api_client.patch(
        f"/api/v1/users/{user.id}/site-role",
        json={"site_role": SiteRole.USER.value},
        headers=auth_headers(admin),
    )

    assert demote_response.status_code == 200
    assert demote_response.json()["site_role"] == SiteRole.USER.value


async def test_user_cannot_change_site_role(
    api_client,
    factories,
    auth_headers,
) -> None:
    actor = await factories.create_user()
    target = await factories.create_user()
    await factories.commit()

    response = await api_client.patch(
        f"/api/v1/users/{target.id}/site-role",
        json={"site_role": SiteRole.ADMIN.value},
        headers=auth_headers(actor),
    )

    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "site_permission_denied"


async def test_admin_cannot_change_own_site_role(
    api_client,
    factories,
    auth_headers,
) -> None:
    admin = await factories.create_user(site_role=SiteRole.ADMIN)
    await factories.commit()

    response = await api_client.patch(
        f"/api/v1/users/{admin.id}/site-role",
        json={"site_role": SiteRole.USER.value},
        headers=auth_headers(admin),
    )

    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "site_permission_denied"


async def test_me_includes_manage_site_roles_permission_for_admin(
    api_client,
    factories,
    auth_headers,
) -> None:
    admin = await factories.create_user(site_role=SiteRole.ADMIN)
    await factories.commit()

    response = await api_client.get("/api/v1/users/me", headers=auth_headers(admin))

    assert response.status_code == 200
    assert SitePermission.MANAGE_SITE_ROLES.value in response.json()["site_permissions"]
