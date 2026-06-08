"""add library_resource_id to character_token_configs

Revision ID: 20260607_0014
Revises: 20260607_0013
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "20260607_0014"
down_revision = "20260607_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c["name"] for c in inspector.get_columns("character_token_configs")}
    existing_fks = {fk.get("name") for fk in inspector.get_foreign_keys("character_token_configs")}

    with op.batch_alter_table("character_token_configs") as batch_op:
        if "library_resource_id" not in existing_columns:
            batch_op.add_column(sa.Column("library_resource_id", sa.Integer(), nullable=True))
        if "fk_character_token_configs_library_resource_id" not in existing_fks:
            batch_op.create_foreign_key(
                "fk_character_token_configs_library_resource_id",
                "library_resources",
                ["library_resource_id"],
                ["id"],
                ondelete="SET NULL",
            )

    existing_indexes = {i["name"] for i in sa.inspect(conn).get_indexes("character_token_configs")}
    if "ix_character_token_configs_library_resource_id" not in existing_indexes:
        op.create_index(
            "ix_character_token_configs_library_resource_id",
            "character_token_configs",
            ["library_resource_id"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = {i["name"] for i in inspector.get_indexes("character_token_configs")}
    if "ix_character_token_configs_library_resource_id" in existing_indexes:
        op.drop_index(
            "ix_character_token_configs_library_resource_id",
            table_name="character_token_configs",
        )

    existing_columns = {c["name"] for c in inspector.get_columns("character_token_configs")}
    if "library_resource_id" in existing_columns:
        with op.batch_alter_table("character_token_configs") as batch_op:
            batch_op.drop_constraint(
                "fk_character_token_configs_library_resource_id",
                type_="foreignkey",
            )
            batch_op.drop_column("library_resource_id")
