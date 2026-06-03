import pytest

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.notifications.models import Notification
from app.modules.rooms.constants import (
    RoomJoinAuditMode,
    RoomJoinRequestAction,
    RoomJoinRequestSource,
    RoomJoinRequestStatus,
    RoomRole,
    RoomVisibility,
)
from app.modules.rooms.join_request.service import RoomJoinRequestService
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomMember
from app.modules.rooms.room.schemas import RoomCreate
from app.modules.rooms.room.service import RoomService


# 验证创建房间时会同时创建 owner 成员关系。
async def test_create_room_creates_owner_membership(db_session, factories) -> None:
    owner = await factories.create_user()
    await factories.commit()

    room = await RoomService().create_room(
        db_session,
        user=owner,
        payload=RoomCreate(name="Watch Party"),
    )

    members = await factories.list_all(RoomMember)

    assert room.name == "Watch Party"
    assert any(member.room_id == room.id and member.user_id == owner.id for member in members)


# 验证非成员无法访问私有房间。
async def test_get_accessible_room_by_id_rejects_private_room_non_member(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    outsider = await factories.create_user()
    room = await factories.create_room(owner=owner, visibility=RoomVisibility.PRIVATE)
    await factories.commit()

    with pytest.raises(ForbiddenError, match="You do not have permission"):
        await RoomService().get_accessible_room_by_id(
            db_session,
            user=outsider,
            room_id=room.id,
        )


# 验证普通成员不能移除房间中的 manager。
async def test_remove_room_member_requires_manager_permission_for_manager_target(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    manager = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=manager, role=RoomRole.MANAGER)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    with pytest.raises(ForbiddenError, match="You do not have permission"):
        await RoomMembershipService().remove_room_member(
            db_session,
            room_id=room.id,
            target_user_id=manager.id,
            current_user=member,
        )


# 验证成员主动退出房间不需要管理权限。
async def test_leave_room_allows_member_without_manage_members_permission(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    await RoomMembershipService().leave_room(
        db_session,
        room_id=room.id,
        user=member,
    )

    membership = await RoomMembershipService().find_room_member(
        db_session,
        room_id=room.id,
        user_id=member.id,
    )
    assert membership is None


# 验证房主不能主动退出房间，只能删除房间。
async def test_leave_room_rejects_owner(db_session, factories) -> None:
    owner = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.commit()

    with pytest.raises(ForbiddenError, match="Owner cannot leave the room"):
        await RoomMembershipService().leave_room(
            db_session,
            room_id=room.id,
            user=owner,
        )


# 验证设置和解除管理员都要求 MANAGE_MANAGERS 权限。
async def test_set_room_member_manager_status_requires_manage_managers(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    manager = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=manager, role=RoomRole.MANAGER)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    with pytest.raises(ForbiddenError, match="You do not have permission"):
        await RoomMembershipService().set_room_member_manager_status(
            db_session,
            room_id=room.id,
            target_user_id=member.id,
            is_manager=True,
            current_user=manager,
        )


# 验证房主可以设置和解除管理员。
async def test_set_room_member_manager_status_updates_role(db_session, factories) -> None:
    owner = await factories.create_user()
    member = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=member, role=RoomRole.MEMBER)
    await factories.commit()

    promoted = await RoomMembershipService().set_room_member_manager_status(
        db_session,
        room_id=room.id,
        target_user_id=member.id,
        is_manager=True,
        current_user=owner,
    )
    assert promoted.role == RoomRole.MANAGER

    demoted = await RoomMembershipService().set_room_member_manager_status(
        db_session,
        room_id=room.id,
        target_user_id=member.id,
        is_manager=False,
        current_user=owner,
    )
    assert demoted.role == RoomRole.MEMBER


# 验证自动通过模式会直接把申请人加入房间而不创建申请记录。
async def test_create_apply_request_auto_approve_adds_member_without_request(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    applicant = await factories.create_user()
    room = await factories.create_room(
        owner=owner,
        join_audit_mode=RoomJoinAuditMode.AUTO_APPROVE,
    )
    await factories.commit()

    request = await RoomJoinRequestService().create_apply_request(
        db_session,
        room_id=room.id,
        user=applicant,
    )

    assert request is None
    member = await RoomMembershipService().find_room_member(
        db_session,
        room_id=room.id,
        user_id=applicant.id,
    )
    assert member is not None


# 验证手动审核模式会创建待处理申请并通知审核人。
async def test_create_apply_request_creates_pending_request_and_notifications(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    reviewer = await factories.create_user()
    applicant = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.add_member(room=room, user=reviewer, role=RoomRole.MANAGER)
    await factories.commit()

    request = await RoomJoinRequestService().create_apply_request(
        db_session,
        room_id=room.id,
        user=applicant,
    )

    notifications = await factories.list_all(Notification)

    assert request is not None
    assert request.status == RoomJoinRequestStatus.PENDING
    assert {item.recipient_user_id for item in notifications} == {owner.id, reviewer.id}


# 验证重复的待处理入房申请会被拒绝。
async def test_create_apply_request_rejects_existing_pending_request(
    db_session,
    factories,
) -> None:
    owner = await factories.create_user()
    applicant = await factories.create_user()
    room = await factories.create_room(owner=owner)
    await factories.create_join_request(room=room, initiator=applicant, target=applicant)
    await factories.commit()

    with pytest.raises(ConflictError, match="Pending request already exists"):
        await RoomJoinRequestService().create_apply_request(
            db_session,
            room_id=room.id,
            user=applicant,
        )


# 验证房间侧审批通过后会完成申请并加入新成员。
async def test_approve_request_by_room_finalizes_membership(db_session, factories) -> None:
    owner = await factories.create_user()
    applicant = await factories.create_user()
    room = await factories.create_room(owner=owner)
    request = await factories.create_join_request(
        room=room,
        initiator=applicant,
        target=applicant,
        source=RoomJoinRequestSource.APPLY,
        status=RoomJoinRequestStatus.PENDING,
        room_action=RoomJoinRequestAction.PENDING,
        target_action=RoomJoinRequestAction.APPROVED,
    )
    await factories.commit()

    updated = await RoomJoinRequestService().approve_request(
        db_session,
        request_id=request.id,
        user=owner,
    )

    member = await RoomMembershipService().find_room_member(
        db_session,
        room_id=room.id,
        user_id=applicant.id,
    )
    assert updated.status == RoomJoinRequestStatus.APPROVED
    assert member is not None
