import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.jobs.wsb_scraper import run_wsb_scrape
from app.jobs.market_scan import run_market_scan

logger = logging.getLogger(__name__)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

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

    scheduler.start()
    logger.info("Background scheduler started with %d jobs", len(scheduler.get_jobs()))
    return scheduler
