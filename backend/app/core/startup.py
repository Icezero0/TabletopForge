from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings
from app.core.logging import log_extra

settings = get_settings()
logger = logging.getLogger("app.startup")


async def ensure_runtime_paths() -> None:
    settings.data_dir_path.mkdir(parents=True, exist_ok=True)
    settings.assets_dir_path.mkdir(parents=True, exist_ok=True)


def _build_alembic_config() -> Config:
    project_root = Path(__file__).resolve().parents[2]
    alembic_ini_path = project_root / "alembic.ini"
    alembic_dir_path = project_root / "alembic"

    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(alembic_dir_path))
    config.set_main_option("sqlalchemy.url", settings.alembic_database_url)
    return config


def _upgrade_database_to_head() -> None:
    command.upgrade(_build_alembic_config(), "head")


def _repair_skipped_assets_hash_migration(config: Config) -> None:
    """DBs that reached tabletop head on the pre-merge chain lack assets.content_hash."""
    engine = create_engine(settings.alembic_database_url)
    try:
        inspector = inspect(engine)
        if not inspector.has_table("assets"):
            return
        if "content_hash" in {column["name"] for column in inspector.get_columns("assets")}:
            return

        with engine.connect() as connection:
            current_revision = MigrationContext.configure(connection).get_current_revision()
        if current_revision != "20260604_0004":
            return

        logger.warning(
            "assets table missing content_hash while alembic is at tabletop head; "
            "applying skipped 20260605_0004 migration",
            **log_extra("startup.migrations_repair_assets_hash"),
        )
        command.stamp(config, "20260604_0003")
        command.upgrade(config, "20260605_0004")
        command.stamp(config, "20260604_0004")
    finally:
        engine.dispose()


async def ensure_database_schema() -> None:
    logger.info(
        "running database migrations to head",
        **log_extra("startup.migrations_start"),
    )
    config = _build_alembic_config()

    def _migrate() -> None:
        _repair_skipped_assets_hash_migration(config)
        _upgrade_database_to_head()

    await asyncio.to_thread(_migrate)
    logger.info(
        "database migrations complete",
        **log_extra("startup.migrations_complete"),
    )


async def initialize_runtime() -> None:
    await ensure_runtime_paths()
    await ensure_database_schema()
