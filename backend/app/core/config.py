from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
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
    max_asset_upload_bytes: int = Field(5 * 1024 * 1024, alias="MAX_ASSET_UPLOAD_BYTES")

    # JWT
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # WS
    ws_auth_timeout_seconds: int = Field(
        10, alias="WS_AUTH_TIMEOUT_SECONDS", ge=1
    )

    # CORS（JWT 走 Authorization 头，无需 cookie；credentials 与 origins=* 在浏览器中互斥）
    cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = Field(False, alias="CORS_ALLOW_CREDENTIALS")

    # LLM（OpenAI 兼容 API，仅后端调用）
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "DASHSCOPE_API_KEY"),
    )
    llm_base_url: str = Field(
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field("qwen-max", alias="LLM_MODEL")
    llm_log_verbose: bool = Field(True, alias="LLM_LOG_VERBOSE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_env(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"development", "dev"}:
                return True
        return value

    @property
    def data_dir_path(self) -> Path:
        return Path(self.data_dir).resolve()

    @property
    def db_path(self) -> Path:
        return (self.data_dir_path / self.db_filename).resolve()

    @property
    def assets_dir_path(self) -> Path:
        return (self.data_dir_path / "assets").resolve()

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path.as_posix()}"

    @property
    def alembic_database_url(self) -> str:
        return self.database_url.replace("+aiosqlite", "")

@lru_cache
def get_settings() -> Settings:
    return Settings()
