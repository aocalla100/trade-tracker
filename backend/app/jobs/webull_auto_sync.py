"""Periodic import of open Webull positions into the trade journal."""

import logging

from app.config import get_settings
from app.db.session import async_session
from app.services.webull_service import WebullService
from app.services.webull_trade_sync import run_webull_import

logger = logging.getLogger(__name__)


async def run_webull_auto_sync():
    """Import new Webull positions as trades (same rules as manual POST /sync/webull)."""
    settings = get_settings()
    if not settings.webull_auto_sync_enabled:
        return
    if not settings.webull_app_key or not settings.webull_app_secret:
        logger.debug("Webull auto-sync skipped: WEBULL_APP_KEY / WEBULL_APP_SECRET not set")
        return

    account_id = (settings.webull_sync_default_account_id or "").strip() or None
    strategy = settings.webull_sync_strategy_name or "webull_positions"
    webull = WebullService()

    try:
        async with async_session() as db:
            result = await run_webull_import(
                db,
                webull,
                account_id=account_id,
                strategy_name=strategy,
            )
        if result.get("error"):
            logger.warning("Webull auto-sync finished with error: %s", result.get("error"))
        else:
            n = result.get("imported", 0)
            if n:
                logger.info(
                    "Webull auto-sync: imported %d new trade(s) for account %s",
                    n,
                    result.get("account_id"),
                )
            else:
                logger.debug(
                    "Webull auto-sync: nothing new (account %s)", result.get("account_id")
                )
    except Exception:
        logger.exception("Webull auto-sync failed")
