"""add character resource sections

Revision ID: 20260620_0035
Revises: 20260618_0034
Create Date: 2026-06-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0035"
down_revision = "20260618_0034"
branch_labels = None
depends_on = None


characters = sa.table(
    "characters",
    sa.column("id", sa.Integer),
    sa.column("resources", sa.JSON),
)


def _with_default_section(resources: object) -> list:
    if not isinstance(resources, list):
        return []
    normalized = []
    changed = False
    for item in resources:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        next_item = dict(item)
        if next_item.get("section") not in ("common", "special"):
            next_item["section"] = "common"
            changed = True
        normalized.append(next_item)
    return normalized if changed else resources


def _without_section(resources: object) -> list:
    if not isinstance(resources, list):
        return []
    normalized = []
    for item in resources:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        next_item = dict(item)
        next_item.pop("section", None)
        normalized.append(next_item)
    return normalized


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.select(characters.c.id, characters.c.resources)).all()
    for character_id, resources in rows:
        next_resources = _with_default_section(resources)
        if next_resources is resources:
            continue
        bind.execute(
            characters.update()
            .where(characters.c.id == character_id)
            .values(resources=next_resources)
        )


def downgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.select(characters.c.id, characters.c.resources)).all()
    for character_id, resources in rows:
        bind.execute(
            characters.update()
            .where(characters.c.id == character_id)
            .values(resources=_without_section(resources))
        )
