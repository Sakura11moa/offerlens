from functools import lru_cache

import httpx
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
    llm_connect_timeout: float = Field(default=5.0, alias="LLM_CONNECT_TIMEOUT")
    llm_read_timeout: float = Field(default=45.0, alias="LLM_READ_TIMEOUT")
    llm_write_timeout: float = Field(default=20.0, alias="LLM_WRITE_TIMEOUT")
    llm_pool_timeout: float = Field(default=10.0, alias="LLM_POOL_TIMEOUT")
    llm_max_retries: int = Field(default=1, alias="LLM_MAX_RETRIES")
    llm_retry_backoff: float = Field(default=1.0, alias="LLM_RETRY_BACKOFF")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip() and self.llm_base_url.strip())

    @property
    def llm_timeout_config(self) -> httpx.Timeout:
        # Keep backward compatibility with LLM_TIMEOUT while allowing split timeouts.
        default_total = max(1.0, float(self.llm_timeout))
        connect = max(0.5, float(self.llm_connect_timeout))
        read = max(1.0, float(self.llm_read_timeout))
        write = max(1.0, float(self.llm_write_timeout))
        pool = max(0.5, float(self.llm_pool_timeout))
        return httpx.Timeout(
            timeout=default_total,
            connect=connect,
            read=read,
            write=write,
            pool=pool,
        )

    @property
    def llm_total_attempts(self) -> int:
        return max(1, int(self.llm_max_retries) + 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
