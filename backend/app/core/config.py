from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "OfferLens Backend"
    app_env: str = Field(default="dev", alias="APP_ENV")

    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_timeout: float = Field(default=30.0, alias="LLM_TIMEOUT")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip() and self.llm_base_url.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
