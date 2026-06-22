"""
Feature Engineering
===================
Computes technical indicators used for ML model training and dashboard visualization.

Indicators implemented:
  - SMA (Simple Moving Average) — 7, 14, 30 periods
  - EMA (Exponential Moving Average)
  - RSI (Relative Strength Index) — ZeroDivisionError fixed
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands (upper, middle, lower)
  - ATR (Average True Range) — volatility
  - OBV (On-Balance Volume)
  - Price target label (for ML classification)
"""
import pandas as pd
import numpy as np
from pathlib import Path

from utils import logger


FEATURES_DIR = Path("data/features")


# ------------------------------------------------------------------
# Moving Averages
# ------------------------------------------------------------------

def add_sma(df: pd.DataFrame, windows: list[int] | None = None, col: str = "close") -> pd.DataFrame:
    """Add Simple Moving Average columns for given window sizes."""
    if windows is None:
        windows = [7, 14, 30]
    for w in windows:
        df[f"sma_{w}"] = df[col].rolling(window=w, min_periods=1).mean()
    return df


def add_ema(df: pd.DataFrame, spans: list[int] | None = None, col: str = "close") -> pd.DataFrame:
    """Add Exponential Moving Average columns."""
    if spans is None:
        spans = [9, 21]
    for s in spans:
        df[f"ema_{s}"] = df[col].ewm(span=s, adjust=False).mean()
    return df


# ------------------------------------------------------------------
# RSI — Fixed ZeroDivisionError
# ------------------------------------------------------------------

def add_rsi(df: pd.DataFrame, period: int = 14, col: str = "close") -> pd.DataFrame:
    """
    Add RSI column. Handles zero average_loss case correctly.
    When all periods are gains → RSI = 100 (not NaN or ZeroDivision).
    """
    delta = df[col].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # Safe division: when avg_loss == 0, RSI = 100 (all gains period)
    rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
    df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

    # Fill initial NaN periods with neutral 50
    df["rsi"] = df["rsi"].fillna(50.0).clip(0, 100)
    return df


# ------------------------------------------------------------------
# MACD
# ------------------------------------------------------------------

def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    col: str = "close",
) -> pd.DataFrame:
    """
    Add MACD line, signal line, and histogram.
    """
    ema_fast = df[col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[col].ewm(span=slow, adjust=False).mean()

    df["macd_line"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]
    return df


# ------------------------------------------------------------------
# Bollinger Bands
# ------------------------------------------------------------------

def add_bollinger_bands(
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    col: str = "close",
) -> pd.DataFrame:
    """
    Add Bollinger Bands (upper, middle, lower) and bandwidth percentage.
    """
    rolling = df[col].rolling(window=window, min_periods=1)
    df["bb_middle"] = rolling.mean()
    bb_std = rolling.std(ddof=0).fillna(0)

    df["bb_upper"] = df["bb_middle"] + num_std * bb_std
    df["bb_lower"] = df["bb_middle"] - num_std * bb_std

    # Bandwidth: distance from lower to upper as % of middle
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"].replace(0, np.nan) * 100
    return df


# ------------------------------------------------------------------
# ATR — Volatility Indicator
# ------------------------------------------------------------------

def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Add Average True Range (volatility measure).
    Requires: high, low, close columns.
    """
    high_low = df["high"] - df["low"]
    high_prev = (df["high"] - df["close"].shift(1)).abs()
    low_prev = (df["low"] - df["close"].shift(1)).abs()

    true_range = pd.concat([high_low, high_prev, low_prev], axis=1).max(axis=1)
    df["atr"] = true_range.ewm(com=period - 1, min_periods=period).mean()
    return df


# ------------------------------------------------------------------
# OBV — Volume Trend Indicator
# ------------------------------------------------------------------

def add_obv(df: pd.DataFrame, price_col: str = "close", volume_col: str = "volume") -> pd.DataFrame:
    """
    On-Balance Volume: cumulative volume flow based on price direction.
    Rising OBV = accumulation (bullish), Falling = distribution (bearish).
    """
    direction = np.sign(df[price_col].diff()).fillna(0)
    df["obv"] = (direction * df[volume_col]).cumsum()
    return df


# ------------------------------------------------------------------
# ML Target Label
# ------------------------------------------------------------------

def add_target_label(
    df: pd.DataFrame,
    lookahead: int = 1,
    threshold_pct: float = 0.5,
    col: str = "close",
) -> pd.DataFrame:
    """
    Compute binary classification target for ML training.
    Label = 1 (bullish) if next N-period return > threshold%, else 0.

    Args:
        lookahead: Number of periods ahead to predict
        threshold_pct: Minimum % price increase to label as bullish
    """
    future_return = (df[col].shift(-lookahead) / df[col] - 1) * 100
    df["target"] = (future_return > threshold_pct).astype(int)
    df["future_return_pct"] = future_return.round(4)
    return df


# ------------------------------------------------------------------
# Master Feature Builder
# ------------------------------------------------------------------

def build_features(df: pd.DataFrame, add_target: bool = True) -> pd.DataFrame:
    """
    Apply all technical indicators to a clean OHLCV DataFrame.
    Returns enriched DataFrame ready for ML training or dashboard display.
    """
    if df.empty:
        logger.warning("[Features] Empty DataFrame passed to build_features.")
        return df

    df = df.copy()

    df = add_sma(df, windows=[7, 14, 30])
    df = add_ema(df, spans=[9, 21])
    df = add_rsi(df, period=14)
    df = add_macd(df)
    df = add_bollinger_bands(df, window=20)
    df = add_atr(df, period=14)
    df = add_obv(df)

    if add_target:
        df = add_target_label(df, lookahead=1, threshold_pct=0.5)

    # Drop rows where all indicators would be NaN (very early rows)
    df = df.dropna(subset=["sma_30", "rsi"]).reset_index(drop=True)

    logger.info(f"[Features] Built {len(df)} rows with {len(df.columns)} features.")
    return df


def save_features(df: pd.DataFrame, symbol: str, suffix: str = "") -> Path:
    """Save feature DataFrame to data/features/ as Parquet."""
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{symbol.lower()}_features{('_' + suffix) if suffix else ''}.parquet"
    path = FEATURES_DIR / fname
    df.to_parquet(path, index=False)
    logger.info(f"[Features] Saved → {path} ({len(df)} rows)")
    return path


if __name__ == "__main__":
    # Smoke test: build features from saved klines
    import json, pathlib

    raw_files = sorted(pathlib.Path("data/raw/binance").glob("klines_BTCUSDT_*.json"))
    if not raw_files:
        logger.error("No klines files. Run: python pipelines/ingestion/binance_client.py first.")
    else:
        from pipelines.transformation.cleaner import parse_klines
        with open(raw_files[-1]) as f:
            raw = json.load(f)
        df_clean = parse_klines(raw)
        df_features = build_features(df_clean)
        print(df_features[["timestamp", "close", "rsi", "macd_line", "bb_upper", "bb_lower", "target"]].tail(10))
        save_features(df_features, "BTC")
