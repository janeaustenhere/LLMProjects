from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Return Evaluation API"
    app_version: str = "0.1.0"

    openrouter_api_key: str = Field("OPENROUTER_API_KEY")
    openai_model : str = Field("OPENAI_MODEL")
    openrouter_temprature : float = Field(
        default = "0.0",
        alias="OPENROUTER_TEMPERATURE")
    policy_file: str = Field(
        default="data/return_policy.txt",
        alias="POLICY_FILE")
    openai_api_base: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias="OPENAI_API_BASE",
    )

    max_upload_bytes : int = 5_000_000
    batch_concurrency: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
