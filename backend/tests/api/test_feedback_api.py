from app.modules.feedback.constants import FeedbackPage, FeedbackStatus, FeedbackType
from app.modules.site.constants import SiteRole


async def test_create_feedback(api_client, factories, auth_headers):
    user = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/feedback",
        data={
            "feedback_type": FeedbackType.BUG.value,
            "page": FeedbackPage.ROOM.value,
            "title": "Room issue",
            "description": "The room state looks stale after joining.",
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["creator_id"] == user.id
    assert body["feedback_type"] == "bug"
    assert body["page"] == "room"
    assert body["status"] == "open"


async def test_user_can_list_and_view_own_feedback(api_client, factories, auth_headers):
    user = await factories.create_user()
    other = await factories.create_user()
    own = await factories.create_feedback(creator=user, title="Mine")
    await factories.create_feedback(creator=other, title="Other")
    await factories.commit()

    list_response = await api_client.get("/api/v1/feedback", headers=auth_headers(user))

    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == own.id

    detail_response = await api_client.get(f"/api/v1/feedback/{own.id}", headers=auth_headers(user))

    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Mine"


async def test_user_cannot_view_other_feedback(api_client, factories, auth_headers):
    user = await factories.create_user()
    other = await factories.create_user()
    feedback = await factories.create_feedback(creator=other)
    await factories.commit()

    response = await api_client.get(f"/api/v1/feedback/{feedback.id}", headers=auth_headers(user))

    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "feedback_permission_denied"


async def test_admin_can_list_and_update_feedback(api_client, factories, auth_headers):
    user = await factories.create_user()
    admin = await factories.create_user(site_role=SiteRole.ADMIN)
    feedback = await factories.create_feedback(creator=user)
    await factories.commit()

    list_response = await api_client.get("/api/v1/feedback/admin", headers=auth_headers(admin))

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    update_response = await api_client.patch(
        f"/api/v1/feedback/admin/{feedback.id}",
        json={"status": FeedbackStatus.REVIEWING.value, "admin_note": "Checking"},
        headers=auth_headers(admin),
    )

    assert update_response.status_code == 200
    body = update_response.json()
    assert body["status"] == "reviewing"
    assert body["admin_note"] == "Checking"
    assert body["handled_by_id"] == admin.id


async def test_non_admin_cannot_access_feedback_admin_api(api_client, factories, auth_headers):
    user = await factories.create_user()
    await factories.commit()

    response = await api_client.get("/api/v1/feedback/admin", headers=auth_headers(user))

    assert response.status_code == 403
    assert response.json()["error"]["reason"] == "site_permission_denied"
