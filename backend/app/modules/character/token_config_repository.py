from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.character.models import CharacterTokenConfig
from app.modules.character.schemas import TokenConfigUpsert


class TokenConfigRepository:
    async def list_by_character(
        self, db: AsyncSession, *, character_id: int
    ) -> list[CharacterTokenConfig]:
        result = await db.execute(
            select(CharacterTokenConfig)
            .where(CharacterTokenConfig.character_id == character_id)
            .order_by(
                CharacterTokenConfig.is_primary.desc(),
                CharacterTokenConfig.sort_order,
            )
        )
        return list(result.scalars().all())

    async def upsert_all(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        configs: list[TokenConfigUpsert],
    ) -> tuple[list[CharacterTokenConfig], set[int], set[int]]:
        """Replace all token configs for a character using upsert logic.
        Items with id are updated; items without id are created; db rows
        whose ids are absent from the payload are deleted.

        Returns (rows, added_lib_ids, removed_lib_ids) so the caller can
        adjust library_resource usage_count accordingly.
        """
        incoming_ids = {c.id for c in configs if c.id is not None}

        existing_rows = await self.list_by_character(db, character_id=character_id)
        existing_by_id = {r.id: r for r in existing_rows}

        added_lib_ids: set[int] = set()
        removed_lib_ids: set[int] = set()

        # Delete rows not in the incoming list
        ids_to_delete = {r.id for r in existing_rows} - incoming_ids
        for row_id in ids_to_delete:
            row = existing_by_id[row_id]
            if row.library_resource_id is not None:
                removed_lib_ids.add(row.library_resource_id)
        if ids_to_delete:
            await db.execute(
                delete(CharacterTokenConfig).where(
                    CharacterTokenConfig.id.in_(ids_to_delete)
                )
            )

        result: list[CharacterTokenConfig] = []
        for cfg in configs:
            if cfg.id is not None and cfg.id in existing_by_id:
                row = existing_by_id[cfg.id]
                old_lib_id = row.library_resource_id
                new_lib_id = cfg.library_resource_id
                if old_lib_id != new_lib_id:
                    if old_lib_id is not None:
                        removed_lib_ids.add(old_lib_id)
                    if new_lib_id is not None:
                        added_lib_ids.add(new_lib_id)
                row.is_primary = cfg.is_primary
                row.name = cfg.name
                row.asset_id = cfg.asset_id
                row.panel_initial = cfg.panel_initial
                row.sort_order = cfg.sort_order
                row.library_resource_id = cfg.library_resource_id
            else:
                row = CharacterTokenConfig(
                    character_id=character_id,
                    is_primary=cfg.is_primary,
                    name=cfg.name,
                    asset_id=cfg.asset_id,
                    panel_initial=cfg.panel_initial,
                    sort_order=cfg.sort_order,
                    library_resource_id=cfg.library_resource_id,
                )
                db.add(row)
                if cfg.library_resource_id is not None:
                    added_lib_ids.add(cfg.library_resource_id)
            result.append(row)

        await db.flush()
        for row in result:
            await db.refresh(row)
        return result, added_lib_ids, removed_lib_ids
