"""Application settings.

1Password/Cursor often mounts ``tradeTracker.env`` as a FIFO (named pipe). Pydantic's
built-in ``env_file`` loader only reads paths where ``Path.is_file()`` is true, which
excludes FIFOs — so we merge layered env files into ``os.environ`` first (including
FIFOs). Later files override earlier ones; values already present in ``os.environ`` are
left unchanged (same behavior as ``python-dotenv`` defaults).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

# trade-tracker/backend/app/config.py -> parents[1]=backend, parents[2]=repo root
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_layered_env_into_os() -> None:
    """Populate os.environ from repo .env files (last file wins); supports FIFO mounts."""
    layers = [
        _REPO_ROOT / ".env",
        _BACKEND_ROOT / ".env",
        _REPO_ROOT / "tradeTracker.env",
        _BACKEND_ROOT / "tradeTracker.env",
    ]
    merged: dict[str, str | None] = {}
    for path in layers:
        if not path.exists():
            continue
        if not (path.is_file() or path.is_fifo()):
            continue
        try:
            data = dotenv_values(path)
        except OSError:
            continue
        if data:
            merged.update(data)
    for key, val in merged.items():
        if val is None or key == "":
            continue
        os.environ.setdefault(key, val)


_load_layered_env_into_os()


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
        # Env files are merged above (FIFO-safe). Pydantic reads from os.environ.
        "env_file": None,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
