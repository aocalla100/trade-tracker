import logging
from datetime import datetime

from app.db.session import async_session
from app.db.models import WsbSentiment
from app.services.reddit_service import RedditService

logger = logging.getLogger(__name__)


async def run_wsb_scrape():
    """Periodic job: scrape WSB, extract tickers, detect sentiment spikes."""
    logger.info("Starting WSB scrape job")

    try:
        reddit = RedditService()
        scraped = reddit.scrape_wsb(limit=100)

        async with async_session() as db:
            spikes = await reddit.detect_spikes(scraped, db)

            for symbol, data in scraped.items():
                record = WsbSentiment(
                    symbol=symbol,
                    mention_count=data["mention_count"],
                    avg_sentiment=round(data["avg_sentiment"], 4),
                    top_posts={"posts": data["top_posts"]},
                    scraped_at=datetime.utcnow(),
                    is_spike=symbol in spikes,
                )
                db.add(record)

            await db.commit()

        logger.info(
            "WSB scrape complete: %d tickers, %d spikes",
            len(scraped),
            len(spikes),
        )
    except Exception as e:
        logger.error("WSB scrape failed: %s", e, exc_info=True)
