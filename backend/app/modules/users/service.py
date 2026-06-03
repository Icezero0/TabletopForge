from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.core.validators import normalize_email
from app.modules.rooms.constants import RoomRole
from app.modules.rooms.room.repository import RoomRepository
from app.modules.site.constants import SitePermission, SiteRole
from app.modules.site.permissions import require_site_permission
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserPatch


class UserService:
    def __init__(self) -> None:
        self.repo = UserRepository()
        self.room_repo = RoomRepository()

    async def create_user(self, db: AsyncSession, payload: UserCreate) -> User:
        if await self.repo.get_by_email(db, payload.email):
            raise ConflictError(
                "Email already exists",
                reason=ErrorReason.EMAIL_ALREADY_EXISTS,
                details={"field": "email"},
            )

        user = await self.repo.create(
            db,
            email=payload.email,
            username=payload.username,
            hashed_password=hash_password(payload.password),
        )
        await db.commit()
        return user

    async def find_user_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        return await self.repo.get_by_id(db, user_id)

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> User:
        user = await self.find_user_by_id(db, user_id)
        if not user:
            raise NotFoundError(
                "User not found",
                reason=ErrorReason.USER_NOT_FOUND,
                details={"user_id": user_id},
            )
        return user

    async def find_user_by_email(self, db: AsyncSession, email: str) -> User | None:
        return await self.repo.get_by_email(db, normalize_email(email))

    async def get_users(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        username: str | None = None,
        email: str | None = None,
    ) -> dict:
        username = username.strip() if username else None
        email = email.strip().lower() if email else None

        items, total = await self.repo.get_users(
            db,
            page=page,
            page_size=page_size,
            username=username,
            email=email,
        )

        total_pages = ceil(total / page_size) if total > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_my_rooms(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int,
        page_size: int,
        role: RoomRole | None = None,
    ) -> dict:
        items, total = await self.room_repo.get_user_rooms(
            db,
            user_id=user.id,
            page=page,
            page_size=page_size,
            role=role,
        )

        total_pages = ceil(total / page_size) if total > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_my_owned_rooms(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int,
        page_size: int,
    ) -> dict:
        return await self.get_my_rooms(
            db,
            user=user,
            page=page,
            page_size=page_size,
            role=RoomRole.OWNER,
        )

    async def patch_me(self, db: AsyncSession, user: User, payload: UserPatch) -> User:
        updates = payload.model_dump(exclude_unset=True)

        if "username" in updates:
            user.username = updates["username"]

        if "password" in updates:
            user.hashed_password = hash_password(updates["password"])

        user = await self.repo.save(db, user)
        await db.commit()
        return user

    async def set_site_role(
        self,
        db: AsyncSession,
        *,
        target_user_id: int,
        site_role: SiteRole,
        actor: User,
    ) -> User:
        require_site_permission(
            SiteRole(actor.site_role),
            SitePermission.MANAGE_SITE_ROLES,
        )

        if actor.id == target_user_id:
            raise ForbiddenError(
                "You cannot change your own site role",
                reason=ErrorReason.SITE_PERMISSION_DENIED,
                details={"user_id": target_user_id},
            )

        target = await self.get_user_by_id(db, target_user_id)
        target.site_role = site_role.value
        target = await self.repo.save(db, target)
        await db.commit()
        return target
