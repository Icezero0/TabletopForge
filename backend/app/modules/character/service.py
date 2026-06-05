from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.character.models import Character
from app.modules.character.repository import CharacterRepository
from app.modules.character.schemas import CharacterListResponse, CharacterResponse
from app.modules.users.models import User


class CharacterService:
    def __init__(self) -> None:
        self.repo = CharacterRepository()

    def _require_owner(self, character: Character, user: User) -> None:
        if character.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to access this character",
                reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
                details={"character_id": character.id},
            )

    async def _get_or_404(self, db: AsyncSession, *, character_id: int) -> Character:
        character = await self.repo.get_by_id(db, character_id=character_id)
        if character is None:
            raise NotFoundError(
                "Character not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"character_id": character_id},
            )
        return character

    async def create_character(
        self,
        db: AsyncSession,
        *,
        user: User,
        name: str,
        player_name: str = "",
        system: str = "dnd5e",
        portrait_asset_id: int | None = None,
        identity: dict | None = None,
        flavor: dict | None = None,
        attributes: dict | None = None,
        features: dict | None = None,
        spells: dict | None = None,
        equipment: dict | None = None,
        extras: dict | None = None,
    ) -> Character:
        character = await self.repo.create(
            db,
            owner_id=user.id,
            name=name,
            player_name=player_name,
            system=system,
            portrait_asset_id=portrait_asset_id,
            identity=identity,
            flavor=flavor,
            attributes=attributes,
            features=features,
            spells=spells,
            equipment=equipment,
            extras=extras,
        )
        await db.commit()
        await db.refresh(character)
        return character

    async def get_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
    ) -> Character:
        character = await self._get_or_404(db, character_id=character_id)
        self._require_owner(character, user)
        return character

    async def list_characters(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> CharacterListResponse:
        offset = (page - 1) * page_size
        items, total = await self.repo.list_by_owner(
            db,
            owner_id=user.id,
            offset=offset,
            limit=page_size,
        )
        return CharacterListResponse(
            items=[CharacterResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )

    async def update_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
        patch_fields: dict,
    ) -> Character:
        character = await self._get_or_404(db, character_id=character_id)
        self._require_owner(character, user)
        updated = await self.repo.update(db, character=character, **patch_fields)
        await db.commit()
        return updated

    async def delete_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
    ) -> None:
        character = await self._get_or_404(db, character_id=character_id)
        self._require_owner(character, user)
        await self.repo.delete(db, character=character)
        await db.commit()

    # =========================
    # Extension points — for internal module use (no ownership check)
    # =========================

    async def get_character_internal(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> Character:
        """Fetch a character without ownership verification. For internal module calls only."""
        return await self._get_or_404(db, character_id=character_id)

    async def require_character_accessible(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
    ) -> Character:
        """Verify a character can be used by this user. Currently: owner only.
        Extend here if sharing or GM-access rules are added."""
        character = await self._get_or_404(db, character_id=character_id)
        self._require_owner(character, user)
        return character
