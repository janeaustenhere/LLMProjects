from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    open_api_key: str = Field(
        alias="OPEN_ROUTER_API_KEY"
    )

    openapi_model: str = Field(
        default="openai/gpt-4.1-mini",
        alias="OPENROUTER_MODEL",
    )

    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )

    shop_api_url: str = Field(
        default="https://hopscotch-shop.vercel.app",
        alias="SHOP_API_URL",
    )

    shop_api_timeout_seconds: float = Field(
        default=30.0,
        alias="SHOP_API_TIMEOUT_SECONDS",
        gt=0,
    )

    agent_recursion_limit: int = Field(
        default=20,
        alias="AGENT_RECURSION_LIMIT",
        ge=4,
        le=100,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
