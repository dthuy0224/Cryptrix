"""
CoinGecko API Client
====================
Fetches market cap, global rankings, and coin metadata.
Uses the free public API (no key required for basic endpoints).
"""
import time
import httpx
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils import logger


BASE_URL = "https://api.coingecko.com/api/v3"
RAW_DATA_DIR = Path("data/raw/coingecko")

# Symbol → CoinGecko ID mapping
COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
}


class CoinGeckoClient:
    """Client for CoinGecko public REST API."""

    def __init__(self, api_key: str | None = None):
        self.headers = {"x-cg-demo-api-key": api_key} if api_key else {}
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def get_markets(
        self,
        symbols: list[str] | None = None,
        vs_currency: str = "usd",
        per_page: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Fetch market data (market cap, price, volume, rank) for top coins.
        Optionally filtered to specific symbols.
        """
        coin_ids = None
        if symbols:
            coin_ids = ",".join(
                COIN_IDS[s.upper()] for s in symbols if s.upper() in COIN_IDS
            )

        params: dict[str, Any] = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": False,
            "price_change_percentage": "24h,7d",
        }
        if coin_ids:
            params["ids"] = coin_ids

        return self._get("/coins/markets", params)

    def get_global(self) -> dict[str, Any]:
        """Fetch global crypto market statistics (total market cap, dominance)."""
        return self._get("/global", {})

    def get_coin_history(self, symbol: str, days: int = 30) -> dict[str, Any]:
        """Fetch historical price, market cap, volume for a coin."""
        coin_id = COIN_IDS.get(symbol.upper())
        if not coin_id:
            raise ValueError(f"Unknown symbol: {symbol}. Add to COIN_IDS map.")
        return self._get(
            f"/coins/{coin_id}/market_chart",
            {"vs_currency": "usd", "days": days, "interval": "hourly"},
        )

    def save_raw(self, data: Any, filename: str) -> Path:
        path = RAW_DATA_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"CoinGecko raw data saved → {path}")
        return path

    def _get(self, endpoint: str, params: dict, retries: int = 3) -> Any:
        url = f"{BASE_URL}{endpoint}"
        delay = 2.0  # CoinGecko free tier: ~30 req/min

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[CoinGecko] GET {endpoint} — attempt {attempt}/{retries}")
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(url, params=params, headers=self.headers)

                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", delay * 2))
                    logger.warning(f"[CoinGecko] Rate-limited. Waiting {wait}s.")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.RequestError as exc:
                logger.error(f"[CoinGecko] Network error attempt {attempt}: {exc}")
                if attempt == retries:
                    raise RuntimeError(f"CoinGecko API failed: {endpoint}") from exc
                time.sleep(delay)
                delay *= 2.0


def ingest_markets(symbols: list[str] | None = None, save: bool = True) -> list[dict]:
    client = CoinGeckoClient()
    data = client.get_markets(symbols)
    if save:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        client.save_raw(data, f"markets_{ts}.json")
    return data


if __name__ == "__main__":
    markets = ingest_markets(["BTC", "ETH", "SOL"])
    for coin in markets:
        logger.info(f"{coin['symbol'].upper()}: ${coin['current_price']:,.2f} | MCap Rank #{coin['market_cap_rank']}")
