from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.character.models import Character


class CharacterRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
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
        character = Character(
            owner_id=owner_id,
            name=name,
            player_name=player_name,
            system=system,
            portrait_asset_id=portrait_asset_id,
            identity=identity or {},
            flavor=flavor or {},
            attributes=attributes or {},
            features=features or {},
            spells=spells,
            equipment=equipment or {},
            extras=extras or {},
        )
        db.add(character)
        await db.flush()
        await db.refresh(character)
        return character

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> Character | None:
        result = await db.execute(
            select(Character).where(Character.id == character_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Character], int]:
        query = select(Character).where(Character.owner_id == owner_id)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(
            query.order_by(Character.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update(
        self,
        db: AsyncSession,
        *,
        character: Character,
        **fields,
    ) -> Character:
        for field, value in fields.items():
            setattr(character, field, value)
        await db.flush()
        await db.refresh(character)
        return character

    async def delete(self, db: AsyncSession, *, character: Character) -> None:
        await db.delete(character)
        await db.flush()
