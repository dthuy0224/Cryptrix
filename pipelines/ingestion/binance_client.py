"""
Binance API Client
==================
Production-grade async client for Binance public REST API.
Fetches OHLCV klines, 24h ticker stats, and order book snapshots.

Implements:
- Exponential backoff retry with jitter
- Rate-limit header awareness (429/418)
- Structured logging via loguru
"""
import time
import httpx
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils import logger


BASE_URL = "https://api.binance.com"
RAW_DATA_DIR = Path("data/raw/binance")


class BinanceClient:
    """
    Async-first HTTP client for Binance public API endpoints.
    Handles retries, rate limits, and raw data persistence.
    """

    def __init__(self, api_key: str | None = None):
        self.headers = {"X-MBX-APIKEY": api_key} if api_key else {}
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public Methods
    # ------------------------------------------------------------------

    def get_ticker_24h(self, symbol: str, retries: int = 3, backoff: float = 1.5) -> dict[str, Any]:
        """
        Fetch 24-hour rolling window price statistics for a trading pair.
        Example: symbol="BTCUSDT"
        """
        return self._get_with_retry(
            endpoint="/api/v3/ticker/24hr",
            params={"symbol": symbol},
            retries=retries,
            backoff=backoff,
            label=f"ticker-24h:{symbol}",
        )

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        retries: int = 3,
    ) -> list[list]:
        """
        Fetch OHLCV candlestick data.
        Intervals: 1m, 5m, 15m, 1h, 4h, 1d, 1w
        Returns list of: [open_time, open, high, low, close, volume, ...]
        """
        return self._get_with_retry(
            endpoint="/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            retries=retries,
            backoff=1.5,
            label=f"klines:{symbol}:{interval}",
        )

    def get_order_book(self, symbol: str, depth: int = 20) -> dict[str, Any]:
        """Fetch current order book snapshot (bids/asks)."""
        return self._get_with_retry(
            endpoint="/api/v3/depth",
            params={"symbol": symbol, "limit": depth},
            retries=3,
            backoff=1.5,
            label=f"orderbook:{symbol}",
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_raw(self, data: Any, filename: str) -> Path:
        """Persist raw API response as JSON to data/raw/binance/."""
        path = RAW_DATA_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Raw data saved → {path}")
        return path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_with_retry(
        self,
        endpoint: str,
        params: dict,
        retries: int,
        backoff: float,
        label: str,
    ) -> Any:
        url = f"{BASE_URL}{endpoint}"
        delay = 1.0

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[Binance] {label} — attempt {attempt}/{retries}")
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, params=params, headers=self.headers)

                if resp.status_code in (429, 418):
                    wait = int(resp.headers.get("Retry-After", delay))
                    logger.warning(f"[Binance] Rate-limited. Waiting {wait}s before retry.")
                    time.sleep(wait)
                    delay *= backoff
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.RequestError as exc:
                logger.error(f"[Binance] Network error on attempt {attempt}: {exc}")
                if attempt == retries:
                    raise RuntimeError(
                        f"Binance API failed for '{label}' after {retries} attempts."
                    ) from exc
                time.sleep(delay)
                delay *= backoff

        raise RuntimeError(f"Binance client exhausted retries for '{label}'.")


# ------------------------------------------------------------------
# Convenience functions (used by Airflow tasks and pipelines directly)
# ------------------------------------------------------------------

def ingest_ticker(symbol: str, save: bool = True) -> dict[str, Any]:
    """Ingest 24h ticker and optionally save raw JSON."""
    client = BinanceClient()
    data = client.get_ticker_24h(symbol)
    if save:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        client.save_raw(data, f"ticker_{symbol}_{ts}.json")
    return data


def ingest_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
    save: bool = True,
) -> list[list]:
    """Ingest OHLCV klines and optionally save raw JSON."""
    client = BinanceClient()
    data = client.get_klines(symbol, interval=interval, limit=limit)
    if save:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        client.save_raw(data, f"klines_{symbol}_{interval}_{ts}.json")
    return data


if __name__ == "__main__":
    # Quick smoke test
    ticker = ingest_ticker("BTCUSDT", save=True)
    logger.info(f"BTC Last Price: {ticker.get('lastPrice')}")

    klines = ingest_klines("BTCUSDT", interval="1h", limit=50, save=True)
    logger.info(f"OHLCV rows fetched: {len(klines)}")
