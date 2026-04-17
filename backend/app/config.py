from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trade_tracker"

    anthropic_api_key: str = ""
    webull_app_key: str = ""
    webull_app_secret: str = ""
    webull_environment: str = "sandbox"

    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "trade-tracker:v1.0"

    cloudflare_api_token: str = ""
    cloudflare_account_id: str = "737e8715349674266a977fe6e53eb038"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
