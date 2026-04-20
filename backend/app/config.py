from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/trade_tracker"

    anthropic_api_key: str = ""
    webull_app_key: str = ""
    webull_app_secret: str = ""
    webull_environment: str = "sandbox"
    # Auto-import open positions into the journal (APScheduler). Manual UI sync still works.
    webull_auto_sync_enabled: bool = True
    webull_auto_sync_interval_hours: float = 6.0
    webull_sync_default_account_id: str = ""
    webull_sync_strategy_name: str = "webull_positions"

    swaggystocks_username: str = ""
    swaggystocks_password: str = ""

    cloudflare_api_token: str = ""
    cloudflare_account_id: str = "737e8715349674266a977fe6e53eb038"

    model_config = {
        "env_file": [
            "../tradeTracker.env", "tradeTracker.env",
            "../.env", ".env",
        ],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
