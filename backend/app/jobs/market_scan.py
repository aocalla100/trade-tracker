import logging

from app.db.session import async_session
from app.db.models import MarketDataCache
from app.services.webull_service import WebullService

logger = logging.getLogger(__name__)

WATCHLIST = ["TSLA", "PLTR", "SPY", "QQQ", "IWM", "TLT"]


async def run_market_scan():
    """Periodic job: fetch snapshots for watchlist symbols and cache them."""
    logger.info("Starting market scan job")

    try:
        webull = WebullService()

        async with async_session() as db:
            for symbol in WATCHLIST:
                try:
                    data = webull.get_snapshot(symbol)
                    if "error" not in data:
                        record = MarketDataCache(
                            symbol=symbol,
                            data_type="snapshot",
                            data=data,
                        )
                        db.add(record)
                except Exception as e:
                    logger.warning("Failed to fetch %s: %s", symbol, e)

            await db.commit()

        logger.info("Market scan complete for %d symbols", len(WATCHLIST))
    except Exception as e:
        logger.error("Market scan failed: %s", e, exc_info=True)
