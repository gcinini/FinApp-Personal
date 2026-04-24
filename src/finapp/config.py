"""Application configuration loaded from environment / .env file."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings (see .env.template)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    db_path: Path = Field(default=Path("./data/finapp.sqlite"), alias="FINAPP_DB_PATH")
    db_encryption_enabled: bool = Field(default=False, alias="FINAPP_DB_ENCRYPTION_ENABLED")
    db_password: str | None = Field(default=None, alias="FINAPP_DB_PASSWORD")

    # Locale
    default_locale: str = Field(default="pt_BR", alias="FINAPP_DEFAULT_LOCALE")
    reporting_currency: str = Field(default="BRL", alias="FINAPP_REPORTING_CURRENCY")

    # FX & market data
    fx_provider: Literal["BCB_PTAX", "ECB", "YAHOO", "MANUAL"] = Field(
        default="BCB_PTAX", alias="FINAPP_FX_PROVIDER"
    )
    market_provider: Literal["YAHOO", "ALPHAVANTAGE"] = Field(
        default="YAHOO", alias="FINAPP_MARKET_PROVIDER"
    )
    alphavantage_api_key: str | None = Field(default=None, alias="ALPHAVANTAGE_API_KEY")

    # AI
    ai_enabled: bool = Field(default=True, alias="FINAPP_AI_ENABLED")
    azure_openai_endpoint: str | None = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str | None = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(
        default="2024-08-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_api_key: str | None = Field(default=None, alias="AZURE_OPENAI_API_KEY")

    # Logging
    log_level: str = Field(default="INFO", alias="FINAPP_LOG_LEVEL")

    @property
    def sqlalchemy_url(self) -> str:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.db_path.as_posix()}"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
