import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.jobs.wsb_scraper import run_wsb_scrape
from app.jobs.market_scan import run_market_scan
from app.jobs.webull_auto_sync import run_webull_auto_sync

logger = logging.getLogger(__name__)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    settings = get_settings()

    scheduler.add_job(
        run_wsb_scrape,
        "interval",
        minutes=30,
        id="wsb_scraper",
        name="WSB Sentiment Scraper",
        misfire_grace_time=300,
    )

    scheduler.add_job(
        run_market_scan,
        "interval",
        hours=1,
        id="market_scan",
        name="Market Opportunity Scanner",
        misfire_grace_time=600,
    )

    interval = float(settings.webull_auto_sync_interval_hours or 0)
    if settings.webull_auto_sync_enabled and interval > 0:
        scheduler.add_job(
            run_webull_auto_sync,
            "interval",
            hours=interval,
            id="webull_trade_sync",
            name="Webull position → trade journal import",
            misfire_grace_time=600,
        )
        logger.info("Webull auto-sync scheduled every %s hours", interval)
    else:
        logger.info(
            "Webull auto-sync off (set WEBULL_AUTO_SYNC_ENABLED=true and "
            "WEBULL_AUTO_SYNC_INTERVAL_HOURS>0 to enable)"
        )

    scheduler.start()
    logger.info("Background scheduler started with %d jobs", len(scheduler.get_jobs()))
    return scheduler
