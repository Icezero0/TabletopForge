from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.character.models import CharacterState


class CharacterStateRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        current_hp: int | None = None,
        max_hp: int | None = None,
        temp_hp: int = 0,
        armor_class: int | None = None,
        conditions: dict | None = None,
        damage_taken: int = 0,
    ) -> CharacterState:
        state = CharacterState(
            character_id=character_id,
            current_hp=current_hp,
            max_hp=max_hp,
            temp_hp=temp_hp,
            armor_class=armor_class,
            conditions=conditions or {},
            damage_taken=damage_taken,
        )
        db.add(state)
        await db.flush()
        await db.refresh(state)
        return state

    async def get_by_character_id(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> CharacterState | None:
        result = await db.execute(
            select(CharacterState).where(CharacterState.character_id == character_id)
        )
        return result.scalar_one_or_none()

    async def get_by_character_ids(
        self,
        db: AsyncSession,
        *,
        character_ids: list[int],
    ) -> dict[int, CharacterState]:
        if not character_ids:
            return {}
        result = await db.execute(
            select(CharacterState).where(CharacterState.character_id.in_(character_ids))
        )
        return {s.character_id: s for s in result.scalars().all()}

    async def update(
        self,
        db: AsyncSession,
        *,
        state: CharacterState,
        **fields: Any,
    ) -> CharacterState:
        for field, value in fields.items():
            setattr(state, field, value)
        await db.flush()
        await db.refresh(state)
        return state
