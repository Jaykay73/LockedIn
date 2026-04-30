from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_default_model: str = "deepseek-v4-flash"
    deepseek_fallback_model: str = "deepseek-v4-pro"

    tavily_api_key: str = ""
    youtube_api_key: str = ""
    search_provider: str = "tavily_youtube"

    max_resources_per_node: int = Field(default=4, ge=2, le=6)
    target_resources_per_node: int = Field(default=3, ge=2, le=4)
    min_resources_per_node: int = Field(default=2, ge=1, le=4)

    roadmap_generation_timeout_seconds: float = Field(default=15, gt=0)
    link_validation_timeout_seconds: float = Field(default=3, gt=0)

    enable_link_validation: bool = True
    enable_cache: bool = True
    enable_demo_fallback: bool = True
    sqlite_db_path: str = "./lockedin_cache.db"

    environment: Literal["development", "production", "test"] = "development"
    log_failed_generations: bool = True
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
