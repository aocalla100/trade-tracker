import re
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import WsbSentiment

logger = logging.getLogger(__name__)
settings = get_settings()

# Common tickers to filter out false positives (common English words)
TICKER_BLACKLIST = {
    "A", "I", "AM", "AN", "AT", "BE", "BY", "DO", "GO", "IF", "IN", "IS",
    "IT", "ME", "MY", "NO", "OF", "OK", "ON", "OR", "SO", "TO", "UP", "US",
    "WE", "AI", "ALL", "ARE", "CAN", "CEO", "DD", "FOR", "GDP", "HAS",
    "HIM", "HOW", "IRS", "LOW", "MAN", "NEW", "NOW", "OLD", "ONE", "OUR",
    "OUT", "OWN", "RUN", "SAY", "SEC", "SET", "THE", "TOP", "TWO", "WAR",
    "WAY", "WHO", "WHY", "WIN", "WON", "YOU", "YOLO", "GAIN", "LOSS",
    "HOLD", "SELL", "CALL", "PUTS", "BEAR", "BULL", "MOON", "PUMP", "DUMP",
    "ROPE", "LMAO", "EDIT", "LINK", "POST", "PART", "LONG", "BEST", "JUST",
    "LIKE", "NEXT", "MOST", "VERY", "MUCH", "NEED", "BEEN", "SOME", "EVER",
    "REAL", "HUGE", "WHAT", "WHEN", "WILL", "GOOD", "OVER", "FREE", "OPEN",
    "HIGH", "CASH", "WISH", "HOPE",
}

TICKER_PATTERN = re.compile(r"\b([A-Z]{1,5})\b")


class RedditService:
    def __init__(self):
        import praw
        self._reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        self._reddit.read_only = True
        self._sub = self._reddit.subreddit("wallstreetbets")

    def scrape_wsb(self, limit: int = 100) -> dict[str, dict]:
        """Scrape hot/new posts, extract tickers, run sentiment analysis.

        Returns a dict of symbol -> {mention_count, avg_sentiment, top_posts, posts}.
        """
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()

        ticker_data: dict[str, dict] = defaultdict(lambda: {
            "mentions": 0,
            "sentiments": [],
            "posts": [],
        })

        for submission in self._sub.hot(limit=limit):
            text = f"{submission.title} {submission.selftext}"
            tickers_found = set(TICKER_PATTERN.findall(text.upper())) - TICKER_BLACKLIST
            sentiment = analyzer.polarity_scores(text)

            for ticker in tickers_found:
                ticker_data[ticker]["mentions"] += 1
                ticker_data[ticker]["sentiments"].append(sentiment["compound"])
                if len(ticker_data[ticker]["posts"]) < 5:
                    ticker_data[ticker]["posts"].append({
                        "id": submission.id,
                        "title": submission.title,
                        "score": submission.score,
                        "url": submission.url,
                        "sentiment": sentiment["compound"],
                    })

        results = {}
        for ticker, data in ticker_data.items():
            if data["mentions"] >= 2:
                results[ticker] = {
                    "mention_count": data["mentions"],
                    "avg_sentiment": (
                        sum(data["sentiments"]) / len(data["sentiments"])
                        if data["sentiments"] else 0
                    ),
                    "top_posts": data["posts"],
                }

        return results

    async def detect_spikes(
        self, current_data: dict[str, dict], db: AsyncSession
    ) -> list[str]:
        """Compare current mention counts to 7-day rolling average.

        Returns list of symbols with >2x spike in mentions.
        """
        week_ago = datetime.utcnow() - timedelta(days=7)
        q = (
            select(
                WsbSentiment.symbol,
                func.avg(WsbSentiment.mention_count).label("avg_mentions"),
            )
            .where(WsbSentiment.scraped_at >= week_ago)
            .group_by(WsbSentiment.symbol)
        )
        result = await db.execute(q)
        historical = {row.symbol: float(row.avg_mentions) for row in result.all()}

        spikes = []
        for symbol, data in current_data.items():
            avg = historical.get(symbol, 0)
            if avg > 0 and data["mention_count"] > avg * 2:
                spikes.append(symbol)
            elif avg == 0 and data["mention_count"] >= 5:
                spikes.append(symbol)

        return spikes
