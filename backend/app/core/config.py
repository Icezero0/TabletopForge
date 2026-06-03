from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 基础
    app_name: str = Field("TabletopForge Backend", alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    debug: bool = Field(True, alias="DEBUG")
    api_v1_prefix: str = "/api/v1"
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_sql: bool = Field(False, alias="LOG_SQL")
    log_access_exclude_paths: list[str] = Field(
        default_factory=lambda: ["/health"],
        alias="LOG_ACCESS_EXCLUDE_PATHS",
    )
    log_uvicorn_access: bool = Field(False, alias="LOG_UVICORN_ACCESS")
    log_uvicorn_level: str = Field("WARNING", alias="LOG_UVICORN_LEVEL")

    # 数据目录 / DB
    data_dir: str = Field("../data", alias="DATA_DIR")
    db_filename: str = Field("TabletopForge.db", alias="DB_FILENAME")

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # WS
    ws_auth_timeout_seconds: int = Field(
        10, alias="WS_AUTH_TIMEOUT_SECONDS", ge=1
    )

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def data_dir_path(self) -> Path:
        return Path(self.data_dir).resolve()

    @property
    def db_path(self) -> Path:
        return (self.data_dir_path / self.db_filename).resolve()

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path.as_posix()}"

    @property
    def alembic_database_url(self) -> str:
        return self.database_url.replace("+aiosqlite", "")

@lru_cache
def get_settings() -> Settings:
    return Settings()
