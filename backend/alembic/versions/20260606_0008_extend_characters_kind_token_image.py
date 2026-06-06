"""extend characters kind and token_image_asset_id

Revision ID: 20260606_0008
Revises: 20260606_0007
Create Date: 2026-06-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0008"
down_revision: str | None = "20260606_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FK_NAME = "fk_characters_token_image_asset_id_assets"
INDEX_NAME = "ix_characters_token_image_asset_id"


def _character_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {col["name"] for col in inspector.get_columns("characters")}


def _character_foreign_key_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {
        fk["name"]
        for fk in inspector.get_foreign_keys("characters")
        if fk.get("name")
    }


def _character_index_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {
        idx["name"]
        for idx in inspector.get_indexes("characters")
        if idx.get("name")
    }


def upgrade() -> None:
    columns = _character_columns()

    if "kind" not in columns:
        with op.batch_alter_table("characters") as batch_op:
            batch_op.add_column(
                sa.Column("kind", sa.String(length=16), server_default="pc", nullable=False),
            )

    columns = _character_columns()
    if "token_image_asset_id" not in columns:
        with op.batch_alter_table("characters") as batch_op:
            batch_op.add_column(
                sa.Column("token_image_asset_id", sa.Integer(), nullable=True),
            )

    fk_names = _character_foreign_key_names()
    index_names = _character_index_names()
    needs_fk = FK_NAME not in fk_names
    needs_index = INDEX_NAME not in index_names
    if not needs_fk and not needs_index:
        return

    with op.batch_alter_table("characters") as batch_op:
        if needs_fk:
            batch_op.create_foreign_key(
                FK_NAME,
                "assets",
                ["token_image_asset_id"],
                ["id"],
                ondelete="SET NULL",
            )
        if needs_index:
            batch_op.create_index(
                INDEX_NAME,
                ["token_image_asset_id"],
                unique=False,
            )


def downgrade() -> None:
    columns = _character_columns()
    fk_names = _character_foreign_key_names()
    index_names = _character_index_names()

    if INDEX_NAME in index_names or FK_NAME in fk_names:
        with op.batch_alter_table("characters") as batch_op:
            if INDEX_NAME in index_names:
                batch_op.drop_index(INDEX_NAME)
            if FK_NAME in fk_names:
                batch_op.drop_constraint(FK_NAME, type_="foreignkey")

    columns = _character_columns()
    if "token_image_asset_id" in columns:
        with op.batch_alter_table("characters") as batch_op:
            batch_op.drop_column("token_image_asset_id")

    columns = _character_columns()
    if "kind" in columns:
        with op.batch_alter_table("characters") as batch_op:
            batch_op.drop_column("kind")
