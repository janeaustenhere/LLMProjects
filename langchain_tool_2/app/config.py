import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    shop_api_url: str
    shop_api_timeout_seconds: float = 30
    llm_timeout_seconds: float = 60
    max_tool_rounds: int = 5
    max_history_message: int = 20

@lru_cache(maxsize=None)
def get_settings() -> Settings:
    return Settings()


