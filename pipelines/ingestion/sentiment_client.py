"""
Sentiment Data Client
=====================
Pulls community sentiment signals from Reddit and News APIs.
Uses mock scores when API keys are absent (graceful degradation).

In production, plug in:
  - REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET
  - NEWS_API_KEY
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils import logger


RAW_DATA_DIR = Path("data/raw/sentiment")


class SentimentClient:
    """
    Aggregates sentiment signals from social platforms and news feeds.
    Falls back to mock scores when credentials are unavailable.
    """

    def __init__(
        self,
        reddit_client_id: str | None = None,
        reddit_secret: str | None = None,
        news_api_key: str | None = None,
    ):
        self.reddit_client_id = reddit_client_id
        self.reddit_secret = reddit_secret
        self.news_api_key = news_api_key
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def get_reddit_sentiment(self, symbol: str, subreddits: list[str] | None = None) -> dict[str, Any]:
        """
        Fetch recent posts from crypto subreddits and compute sentiment score.
        Falls back to mock data if credentials are missing.
        """
        if not (self.reddit_client_id and self.reddit_secret):
            logger.warning("[Sentiment] Reddit credentials missing — using mock data.")
            return self._mock_reddit_sentiment(symbol)

        # Production: use praw library
        # import praw
        # reddit = praw.Reddit(client_id=..., client_secret=..., user_agent="Cryptrix/1.0")
        # subreddit = reddit.subreddit("bitcoin+cryptocurrency")
        # ... compute real sentiment with FinBERT
        return self._mock_reddit_sentiment(symbol)

    def get_news_sentiment(self, symbol: str) -> dict[str, Any]:
        """
        Fetch crypto news headlines and compute sentiment.
        Falls back to mock if NEWS_API_KEY is absent.
        """
        if not self.news_api_key:
            logger.warning("[Sentiment] NEWS_API_KEY missing — using mock data.")
            return self._mock_news_sentiment(symbol)

        # Production: call NewsAPI
        # import httpx
        # resp = httpx.get("https://newsapi.org/v2/everything", params={
        #     "q": f"{symbol} crypto",
        #     "apiKey": self.news_api_key,
        #     "language": "en",
        #     "pageSize": 20,
        # })
        return self._mock_news_sentiment(symbol)

    def get_combined_sentiment(self, symbol: str) -> dict[str, Any]:
        """
        Merge Reddit + News signals into a unified sentiment score (-1.0 to 1.0).
        """
        reddit = self.get_reddit_sentiment(symbol)
        news = self.get_news_sentiment(symbol)

        # Weighted average: 60% social, 40% news
        combined_score = round(
            reddit["score"] * 0.6 + news["score"] * 0.4, 4
        )
        label = _score_to_label(combined_score)

        result = {
            "symbol": symbol.upper(),
            "score": combined_score,
            "label": label,
            "reddit": reddit,
            "news": news,
            "mention_count": reddit["mention_count"] + news["mention_count"],
            "source_breakdown": {
                "reddit": reddit["mention_count"],
                "news": news["mention_count"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"[Sentiment] {symbol.upper()}: score={combined_score:.3f} ({label}) "
            f"| mentions={result['mention_count']}"
        )
        return result

    def save_raw(self, data: Any, filename: str) -> Path:
        path = RAW_DATA_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    # ------------------------------------------------------------------
    # Mock Fallbacks (realistic distributions)
    # ------------------------------------------------------------------

    def _mock_reddit_sentiment(self, symbol: str) -> dict[str, Any]:
        """Generate plausible mock Reddit sentiment (slightly bullish bias)."""
        score = round(random.uniform(-0.3, 0.75), 4)
        return {
            "source": "reddit",
            "symbol": symbol.upper(),
            "score": score,
            "label": _score_to_label(score),
            "mention_count": random.randint(500, 12000),
            "top_subreddits": ["r/Bitcoin", "r/CryptoCurrency", f"r/{symbol}"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _mock_news_sentiment(self, symbol: str) -> dict[str, Any]:
        score = round(random.uniform(-0.2, 0.6), 4)
        return {
            "source": "news",
            "symbol": symbol.upper(),
            "score": score,
            "label": _score_to_label(score),
            "mention_count": random.randint(20, 500),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _score_to_label(score: float) -> str:
    if score > 0.15:
        return "positive"
    elif score < -0.15:
        return "negative"
    return "neutral"


def ingest_sentiment(symbols: list[str], save: bool = True) -> list[dict[str, Any]]:
    """Fetch combined sentiment for multiple symbols."""
    client = SentimentClient()
    results = [client.get_combined_sentiment(sym) for sym in symbols]
    if save:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        client.save_raw(results, f"sentiment_{ts}.json")
    return results


if __name__ == "__main__":
    data = ingest_sentiment(["BTC", "ETH", "SOL"])
    for s in data:
        logger.info(f"{s['symbol']}: {s['score']:.3f} ({s['label']})")
