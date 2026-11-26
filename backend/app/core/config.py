from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Commerce Order Console API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:password@localhost:5434/commerce_console"
    cors_origins: list[str] = ["http://localhost:3000"]
    # Products with 1..threshold units are "low stock"; 0 units is counted as "out of stock".
    low_stock_threshold: int = Field(default=5, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
