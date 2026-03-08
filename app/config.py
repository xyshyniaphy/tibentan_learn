from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    anthropic_auth_token: str = ""
    anthropic_base_url: str = "https://api.z.ai/api/anthropic"
    database_url: str = "sqlite:///./data/tibetan.db"
    ip_whitelist: str = "127.0.0.1,::1"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
