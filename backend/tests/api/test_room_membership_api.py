from unittest.mock import AsyncMock

from app.modules.rooms.constants import GameRole, RoomRole
from app.modules.rooms.models import RoomMember


# 验证普通成员可以主动退出房间，并触发会话清理和成员列表广播。
async def test_leave_room_removes_current_member_and_publishes_members(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    app.state.realtime_publisher.publish_room_members = AsyncMock()
    app.state.realtime_room_presence_service.find_room_user_connection = AsyncMock(
        return_value=None
    )

    response = await api_client.delete(
        f"/api/v1/rooms/{room.id}/members/me",
        headers=auth_headers(member),
    )

    assert response.status_code == 204

    members = await factories.list_all(RoomMember)
    assert all(item.user_id != member.id for item in members)
    assert any(item.user_id == owner.id for item in members)
    app.state.realtime_publisher.publish_room_members.assert_awaited_once_with(
        room_id=room.id
    )


# 验证房主不能通过退出成员关系离开自己创建的房间。
async def test_leave_room_rejects_owner(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    response = await api_client.delete(
        f"/api/v1/rooms/{room.id}/members/me",
        headers=auth_headers(owner),
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Owner cannot leave the room"


# 验证具备 MANAGE_MANAGERS 权限的房主可以把普通成员设置为管理员。
async def test_set_room_member_manager_promotes_member(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    app.state.realtime_publisher.publish_room_members = AsyncMock()

    response = await api_client.put(
        f"/api/v1/rooms/{room.id}/members/{member.id}/manager",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200
    assert response.json()["room_role"] == RoomRole.MANAGER
    assert response.json()["game_role"] == GameRole.PL

    members = await factories.list_all(RoomMember)
    updated = next(item for item in members if item.user_id == member.id)
    assert updated.role == RoomRole.MANAGER
    app.state.realtime_publisher.publish_room_members.assert_awaited_once_with(
        room_id=room.id
    )


# 验证具备 MANAGE_MANAGERS 权限的房主可以解除管理员。
async def test_unset_room_member_manager_demotes_manager(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    manager = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=manager, role=RoomRole.MANAGER)
    await factories.commit()

    app.state.realtime_publisher.publish_room_members = AsyncMock()

    response = await api_client.delete(
        f"/api/v1/rooms/{room.id}/members/{manager.id}/manager",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200
    assert response.json()["room_role"] == RoomRole.MEMBER
    assert response.json()["game_role"] == GameRole.PL

    members = await factories.list_all(RoomMember)
    updated = next(item for item in members if item.user_id == manager.id)
    assert updated.role == RoomRole.MEMBER
    app.state.realtime_publisher.publish_room_members.assert_awaited_once_with(
        room_id=room.id
    )


# 验证普通管理员没有 MANAGE_MANAGERS 权限，不能设置其他管理员。
async def test_set_room_member_manager_requires_manage_managers(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    manager = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=manager, role=RoomRole.MANAGER)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    response = await api_client.put(
        f"/api/v1/rooms/{room.id}/members/{member.id}/manager",
        headers=auth_headers(manager),
    )

    assert response.status_code == 403


async def test_create_room_defaults_owner_game_role_to_gm(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/rooms",
        headers=auth_headers(owner),
        json={"name": "Campaign Alpha"},
    )

    assert response.status_code == 201
    room_id = response.json()["id"]

    members_response = await api_client.get(
        f"/api/v1/rooms/{room_id}/members",
        headers=auth_headers(owner),
    )
    assert members_response.status_code == 200
    owner_member = next(
        item for item in members_response.json()["items"] if item["user_id"] == owner.id
    )
    assert owner_member["room_role"] == RoomRole.OWNER
    assert owner_member["game_role"] == GameRole.GM


async def test_create_room_creator_can_choose_pl_game_role(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    await factories.commit()

    response = await api_client.post(
        "/api/v1/rooms",
        headers=auth_headers(owner),
        json={"name": "Player Host", "creator_game_role": "PL"},
    )

    assert response.status_code == 201
    room_id = response.json()["id"]

    members_response = await api_client.get(
        f"/api/v1/rooms/{room_id}/members",
        headers=auth_headers(owner),
    )
    owner_member = next(
        item for item in members_response.json()["items"] if item["user_id"] == owner.id
    )
    assert owner_member["game_role"] == GameRole.PL


async def test_patch_member_game_role_orthogonal_to_room_role(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    app.state.realtime_publisher.publish_room_members = AsyncMock()

    response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/members/{member.id}/game-role",
        headers=auth_headers(owner),
        json={"game_role": "GM"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["room_role"] == RoomRole.MEMBER
    assert body["game_role"] == GameRole.GM

    members = await factories.list_all(RoomMember)
    updated = next(item for item in members if item.user_id == member.id)
    assert updated.role == RoomRole.MEMBER
    assert updated.game_role == GameRole.GM


async def test_manager_can_patch_owner_game_role(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    manager = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=manager, role=RoomRole.MANAGER)
    await factories.commit()

    app.state.realtime_publisher.publish_room_members = AsyncMock()

    response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/members/{owner.id}/game-role",
        headers=auth_headers(manager),
        json={"game_role": "PL"},
    )

    assert response.status_code == 200
    assert response.json()["room_role"] == RoomRole.OWNER
    assert response.json()["game_role"] == GameRole.PL


async def test_list_members_auto_assigns_player_color(
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    response = await api_client.get(
        f"/api/v1/rooms/{room.id}/members",
        headers=auth_headers(member),
    )

    assert response.status_code == 200
    items = response.json()["items"]
    colors = {item["player_color"] for item in items}
    assert all(color and color.startswith("#") for color in colors)
    assert len(colors) == len(items)


async def test_patch_my_player_color_rejects_taken_color(
    app,
    api_client,
    factories,
    auth_headers,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    list_response = await api_client.get(
        f"/api/v1/rooms/{room.id}/members",
        headers=auth_headers(member),
    )
    owner_color = next(
        item["player_color"]
        for item in list_response.json()["items"]
        if item["user_id"] == owner.id
    )

    app.state.realtime_publisher.publish_room_members = AsyncMock()

    response = await api_client.patch(
        f"/api/v1/rooms/{room.id}/members/me/player-color",
        headers=auth_headers(member),
        json={"player_color": owner_color},
    )

    assert response.status_code == 409
