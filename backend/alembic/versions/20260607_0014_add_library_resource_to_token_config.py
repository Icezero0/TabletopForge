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
    existing_columns = {c["name"] for c in sa.inspect(conn).get_columns("character_token_configs")}

    if "library_resource_id" not in existing_columns:
        op.add_column(
            "character_token_configs",
            sa.Column(
                "library_resource_id",
                sa.Integer(),
                sa.ForeignKey("library_resources.id", ondelete="SET NULL"),
                nullable=True,
            ),
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
    op.drop_index(
        "ix_character_token_configs_library_resource_id",
        table_name="character_token_configs",
    )
    op.drop_column("character_token_configs", "library_resource_id")
