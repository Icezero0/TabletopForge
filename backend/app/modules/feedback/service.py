from datetime import datetime, timezone
from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.error_reasons import ErrorReason
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.feedback.constants import FeedbackPage, FeedbackStatus, FeedbackType
from app.modules.feedback.models import Feedback
from app.modules.feedback.repository import FeedbackRepository
from app.modules.feedback.schemas import (
    FeedbackUpdateRequest,
    normalize_feedback_description,
    normalize_feedback_title,
)
from app.modules.site.constants import SitePermission, SiteRole
from app.modules.site.permissions import require_site_permission
from app.modules.users.models import User


class FeedbackService:
    def __init__(self) -> None:
        self.repo = FeedbackRepository()
        self.asset_service = AssetService()

    def _site_role(self, user: User) -> SiteRole:
        try:
            return SiteRole(user.site_role)
        except ValueError:
            return SiteRole.USER

    def _require(self, user: User, permission: SitePermission) -> None:
        require_site_permission(self._site_role(user), permission)

    def _can_view_all_feedback(self, user: User) -> bool:
        try:
            self._require(user, SitePermission.VIEW_ALL_FEEDBACK)
            return True
        except ForbiddenError:
            return False

    async def create_feedback(
        self,
        db: AsyncSession,
        *,
        user: User,
        feedback_type: FeedbackType,
        page: FeedbackPage,
        title: str,
        description: str,
        images: list[UploadFile] | None = None,
    ) -> Feedback:
        self._require(user, SitePermission.CREATE_FEEDBACK)
        normalized_title = normalize_feedback_title(title)
        normalized_description = normalize_feedback_description(description)

        feedback = await self.repo.create_feedback(
            db,
            creator_id=user.id,
            feedback_type=feedback_type.value,
            page=page.value,
            title=normalized_title,
            description=normalized_description,
        )

        for image in images or []:
            await self.asset_service.create_image_asset(
                db,
                file=image,
                asset_type=AssetType.FEEDBACK_IMAGE,
                owner_id=user.id,
                feedback_id=feedback.id,
            )
        await db.commit()

        stored = await self.repo.find_feedback_by_id(db, feedback.id)
        if stored is None:
            raise RuntimeError("Feedback not found after creation")
        return stored

    async def get_my_feedbacks(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int,
        page_size: int,
        status: FeedbackStatus | None = None,
        feedback_type: FeedbackType | None = None,
        feedback_page: FeedbackPage | None = None,
    ) -> dict:
        self._require(user, SitePermission.VIEW_OWN_FEEDBACK)
        items, total = await self.repo.get_feedbacks(
            db,
            creator_id=user.id,
            page=page,
            page_size=page_size,
            status=status.value if status else None,
            feedback_type=feedback_type.value if feedback_type else None,
            feedback_page=feedback_page.value if feedback_page else None,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if total else 0,
        }

    async def get_all_feedbacks(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int,
        page_size: int,
        status: FeedbackStatus | None = None,
        feedback_type: FeedbackType | None = None,
        feedback_page: FeedbackPage | None = None,
    ) -> dict:
        self._require(user, SitePermission.VIEW_ALL_FEEDBACK)
        items, total = await self.repo.get_feedbacks(
            db,
            page=page,
            page_size=page_size,
            status=status.value if status else None,
            feedback_type=feedback_type.value if feedback_type else None,
            feedback_page=feedback_page.value if feedback_page else None,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if total else 0,
        }

    async def get_feedback(
        self,
        db: AsyncSession,
        *,
        feedback_id: int,
        user: User,
    ) -> Feedback:
        feedback = await self.repo.find_feedback_by_id(db, feedback_id)
        if feedback is None:
            raise NotFoundError(
                "Feedback not found",
                reason=ErrorReason.FEEDBACK_NOT_FOUND,
                details={"feedback_id": feedback_id},
            )

        if feedback.creator_id != user.id and not self._can_view_all_feedback(user):
            raise ForbiddenError(
                "You do not have permission to view this feedback",
                reason=ErrorReason.FEEDBACK_PERMISSION_DENIED,
                details={"feedback_id": feedback_id},
            )

        return feedback

    async def update_feedback(
        self,
        db: AsyncSession,
        *,
        feedback_id: int,
        payload: FeedbackUpdateRequest,
        user: User,
    ) -> Feedback:
        self._require(user, SitePermission.UPDATE_FEEDBACK)
        feedback = await self.repo.find_feedback_by_id(db, feedback_id)
        if feedback is None:
            raise NotFoundError(
                "Feedback not found",
                reason=ErrorReason.FEEDBACK_NOT_FOUND,
                details={"feedback_id": feedback_id},
            )

        if payload.status is not None:
            feedback.status = payload.status.value
            feedback.handled_by_id = user.id
            feedback.handled_at = datetime.now(timezone.utc)

        if payload.admin_note is not None:
            feedback.admin_note = payload.admin_note
            feedback.handled_by_id = user.id
            feedback.handled_at = datetime.now(timezone.utc)

        await self.repo.save_feedback(db, feedback)
        await db.commit()

        stored = await self.repo.find_feedback_by_id(db, feedback.id)
        if stored is None:
            raise RuntimeError("Feedback not found after update")
        return stored

