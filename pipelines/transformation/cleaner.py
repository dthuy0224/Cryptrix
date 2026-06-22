"""
Data Cleaner
============
Normalizes raw API responses into clean, typed pandas DataFrames.
Handles: missing values, duplicates, type casting, outlier flagging.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Any

from utils import logger


# ------------------------------------------------------------------
# Binance Klines → OHLCV DataFrame
# ------------------------------------------------------------------

KLINE_COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_volume", "trade_count",
    "taker_buy_base_volume", "taker_buy_quote_volume", "ignore",
]


def parse_klines(raw_klines: list[list]) -> pd.DataFrame:
    """
    Convert raw Binance klines list to a clean OHLCV DataFrame.

    Args:
        raw_klines: Raw response from Binance /api/v3/klines

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    if not raw_klines:
        logger.warning("[Cleaner] Empty klines data received.")
        return pd.DataFrame()

    df = pd.DataFrame(raw_klines, columns=KLINE_COLUMNS)

    # Convert timestamps (ms → datetime UTC)
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)

    # Cast price/volume columns to float
    numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
    df[numeric_cols] = df[numeric_cols].astype(float)

    # Drop duplicates on timestamp
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    # Keep only useful columns
    df = df[["timestamp", "open", "high", "low", "close", "volume", "quote_volume", "trade_count"]]
    df["trade_count"] = df["trade_count"].astype(int)

    logger.info(f"[Cleaner] Parsed {len(df)} OHLCV rows | {df['timestamp'].min()} → {df['timestamp'].max()}")
    return df


# ------------------------------------------------------------------
# Binance Ticker → Clean dict
# ------------------------------------------------------------------

def parse_ticker_24h(raw: dict[str, Any], symbol: str | None = None) -> dict[str, Any]:
    """
    Normalize raw Binance 24h ticker into a clean typed dict.

    Returns:
        {symbol, price, change_24h_pct, volume_24h, high_24h, low_24h, timestamp}
    """
    try:
        clean = {
            "symbol": (symbol or raw.get("symbol", "UNKNOWN")).replace("USDT", ""),
            "price": float(raw["lastPrice"]),
            "change_24h_pct": float(raw["priceChangePercent"]),
            "change_24h_abs": float(raw["priceChange"]),
            "volume_24h": float(raw["volume"]),
            "quote_volume_24h": float(raw["quoteVolume"]),
            "high_24h": float(raw["highPrice"]),
            "low_24h": float(raw["lowPrice"]),
            "open_price": float(raw["openPrice"]),
            "trade_count": int(raw["count"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return clean
    except (KeyError, ValueError) as e:
        logger.error(f"[Cleaner] Failed to parse ticker: {e}")
        raise


# ------------------------------------------------------------------
# CoinGecko Markets → DataFrame
# ------------------------------------------------------------------

def parse_coingecko_markets(raw: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Normalize CoinGecko /coins/markets response to a clean DataFrame.
    """
    if not raw:
        return pd.DataFrame()

    records = []
    for coin in raw:
        records.append({
            "symbol": coin.get("symbol", "").upper(),
            "name": coin.get("name"),
            "price": coin.get("current_price"),
            "market_cap": coin.get("market_cap"),
            "market_cap_rank": coin.get("market_cap_rank"),
            "volume_24h": coin.get("total_volume"),
            "change_24h_pct": coin.get("price_change_percentage_24h"),
            "change_7d_pct": coin.get("price_change_percentage_7d_in_currency"),
            "circulating_supply": coin.get("circulating_supply"),
            "ath": coin.get("ath"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    df = pd.DataFrame(records).dropna(subset=["price", "market_cap"])
    logger.info(f"[Cleaner] Parsed {len(df)} CoinGecko market rows.")
    return df


# ------------------------------------------------------------------
# Data Quality Checks
# ------------------------------------------------------------------

def check_ohlcv_quality(df: pd.DataFrame) -> dict[str, Any]:
    """
    Run basic quality checks on an OHLCV DataFrame.
    Returns a quality report dict.
    """
    if df.empty:
        return {"status": "empty", "issues": ["DataFrame is empty"]}

    issues = []

    # Check for nulls
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            issues.append(f"Column '{col}' has {count} null values")

    # Check for price anomalies (close > 5x open in single candle)
    suspicious = df[df["close"] > df["open"] * 5]
    if not suspicious.empty:
        issues.append(f"{len(suspicious)} candles with >500% price spike detected")

    # Check for zero/negative prices
    if (df["close"] <= 0).any():
        issues.append("Zero or negative close prices detected")

    # Duplicate timestamps
    dupes = df["timestamp"].duplicated().sum()
    if dupes > 0:
        issues.append(f"{dupes} duplicate timestamps found")

    status = "clean" if not issues else "issues_found"
    report = {
        "status": status,
        "row_count": len(df),
        "date_range": {
            "start": str(df["timestamp"].min()),
            "end": str(df["timestamp"].max()),
        },
        "null_counts": null_counts.to_dict(),
        "issues": issues,
    }

    if issues:
        logger.warning(f"[QA] Data quality issues: {issues}")
    else:
        logger.info(f"[QA] OHLCV data passed quality checks. Rows: {len(df)}")

    return report


if __name__ == "__main__":
    # Smoke test with saved raw data
    import json, pathlib

    raw_files = list(pathlib.Path("data/raw/binance").glob("klines_*.json"))
    if raw_files:
        with open(raw_files[-1]) as f:
            raw = json.load(f)
        df = parse_klines(raw)
        report = check_ohlcv_quality(df)
        print(df.tail())
        print(report)
    else:
        logger.warning("No raw klines files found. Run binance_client.py first.")
