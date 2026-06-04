from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.users.models import User, UserAvatarHistory


class UserRepository:
    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_users(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        username: str | None = None,
        email: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        conditions = []

        if username:
            username_like = f"%{username.lower()}%"
            conditions.append(func.lower(User.username).like(username_like))

        if email:
            email_like = f"%{email.lower()}%"
            conditions.append(func.lower(User.email).like(email_like))

        if conditions:
            filter_expr = or_(*conditions)
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        stmt = (
            stmt.order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        total = await db.scalar(count_stmt)
        return items, int(total or 0)

    async def create(
        self,
        db: AsyncSession,
        *,
        email: str,
        username: str | None,
        hashed_password: str,
    ) -> User:
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def save(self, db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def create_avatar_history(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        asset_id: int,
    ) -> UserAvatarHistory:
        history = UserAvatarHistory(user_id=user_id, asset_id=asset_id)
        db.add(history)
        await db.flush()
        await db.refresh(history)
        return history

    async def get_avatar_history(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[UserAvatarHistory], int]:
        stmt = (
            select(UserAvatarHistory)
            .options(joinedload(UserAvatarHistory.asset))
            .where(UserAvatarHistory.user_id == user_id)
            .order_by(UserAvatarHistory.created_at.desc(), UserAvatarHistory.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_stmt = (
            select(func.count())
            .select_from(UserAvatarHistory)
            .where(UserAvatarHistory.user_id == user_id)
        )

        result = await db.execute(stmt)
        items = list(result.scalars().all())
        total = await db.scalar(count_stmt)
        return items, int(total or 0)
