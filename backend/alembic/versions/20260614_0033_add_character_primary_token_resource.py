"""bind characters to primary token resources

Revision ID: 20260614_0033
Revises: 20260614_0032
Create Date: 2026-06-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260614_0033"
down_revision: str | None = "20260614_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("characters") as batch_op:
        batch_op.add_column(sa.Column("primary_token_resource_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_characters_primary_token_resource_id",
            ["primary_token_resource_id"],
        )
        batch_op.create_foreign_key(
            "fk_characters_primary_token_resource_id_library_resources",
            "library_resources",
            ["primary_token_resource_id"],
            ["id"],
            ondelete="SET NULL",
        )

    bind = op.get_bind()
    metadata = sa.MetaData()
    characters = sa.Table(
        "characters",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_id", sa.Integer),
        sa.Column("name", sa.String),
        sa.Column("portrait_asset_id", sa.Integer),
        sa.Column("token_image_asset_id", sa.Integer),
        sa.Column("primary_token_resource_id", sa.Integer),
    )
    library_resources = sa.Table(
        "library_resources",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("owner_id", sa.Integer),
        sa.Column("type", sa.String),
        sa.Column("name", sa.String),
        sa.Column("primary_asset_id", sa.Integer),
        sa.Column("meta", sa.JSON),
        sa.Column("usage_count", sa.Integer),
    )
    assets = sa.Table(
        "assets",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ref_count", sa.Integer),
    )

    rows = bind.execute(
        sa.select(
            characters.c.id,
            characters.c.owner_id,
            characters.c.name,
            characters.c.portrait_asset_id,
            characters.c.token_image_asset_id,
        )
    ).mappings()
    for row in rows:
        asset_id = row["token_image_asset_id"] or row["portrait_asset_id"]
        result = bind.execute(
            library_resources.insert().values(
                owner_id=row["owner_id"],
                type="token",
                name=row["name"],
                primary_asset_id=asset_id,
                meta={
                    "generated_from": "character_primary_token",
                    "character_id": row["id"],
                },
                usage_count=1,
            )
        )
        resource_id = result.inserted_primary_key[0]
        bind.execute(
            characters.update()
            .where(characters.c.id == row["id"])
            .values(primary_token_resource_id=resource_id)
        )
        if asset_id is not None:
            bind.execute(
                assets.update()
                .where(assets.c.id == asset_id)
                .values(ref_count=assets.c.ref_count + 1)
            )


def downgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    characters = sa.Table(
        "characters",
        metadata,
        sa.Column("primary_token_resource_id", sa.Integer),
    )
    library_resources = sa.Table(
        "library_resources",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usage_count", sa.Integer),
    )

    resource_ids = [
        row[0]
        for row in bind.execute(
            sa.select(characters.c.primary_token_resource_id).where(
                characters.c.primary_token_resource_id.is_not(None)
            )
        )
    ]
    for resource_id in resource_ids:
        bind.execute(
            library_resources.update()
            .where(library_resources.c.id == resource_id)
            .values(
                usage_count=sa.case(
                    (library_resources.c.usage_count > 0, library_resources.c.usage_count - 1),
                    else_=0,
                )
            )
        )

    with op.batch_alter_table("characters") as batch_op:
        batch_op.drop_constraint(
            "fk_characters_primary_token_resource_id_library_resources",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_characters_primary_token_resource_id")
        batch_op.drop_column("primary_token_resource_id")
