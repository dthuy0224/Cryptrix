"""
Local Data Loader
=================
Saves processed DataFrames to local storage (CSV/Parquet).
Designed with the same interface as future GCS/BigQuery loaders
so swapping to cloud storage requires minimal code changes.
"""
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from utils import logger


PROCESSED_DIR = Path("data/processed")
FEATURES_DIR = Path("data/features")


class LocalLoader:
    """
    Persists clean/transformed data to local filesystem.
    Interface mirrors GCSLoader/BigQueryLoader for easy swap.
    """

    def __init__(self):
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    def save_ohlcv(self, df: pd.DataFrame, symbol: str, interval: str = "1h") -> Path:
        """Save clean OHLCV DataFrame as Parquet."""
        path = PROCESSED_DIR / f"{symbol.lower()}_{interval}_ohlcv.parquet"
        df.to_parquet(path, index=False)
        logger.info(f"[Loader] OHLCV saved → {path} ({len(df)} rows)")
        return path

    def save_ticker(self, data: dict, symbol: str) -> Path:
        """Append ticker snapshot to a rolling CSV file."""
        path = PROCESSED_DIR / f"{symbol.lower()}_tickers.csv"
        row = pd.DataFrame([data])
        if path.exists():
            row.to_csv(path, mode="a", header=False, index=False)
        else:
            row.to_csv(path, index=False)
        logger.info(f"[Loader] Ticker appended → {path}")
        return path

    def save_sentiment(self, data: list[dict], suffix: str = "") -> Path:
        """Save sentiment results as JSON-lines CSV."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        fname = f"sentiment_{ts}{('_' + suffix) if suffix else ''}.csv"
        path = PROCESSED_DIR / fname
        df = pd.DataFrame(data)
        if path.exists():
            df.to_csv(path, mode="a", header=False, index=False)
        else:
            df.to_csv(path, index=False)
        logger.info(f"[Loader] Sentiment saved → {path}")
        return path

    def save_features(self, df: pd.DataFrame, symbol: str) -> Path:
        """Save feature-engineered DataFrame as Parquet."""
        path = FEATURES_DIR / f"{symbol.lower()}_features.parquet"
        df.to_parquet(path, index=False)
        logger.info(f"[Loader] Features saved → {path} ({len(df)} rows)")
        return path

    def load_ohlcv(self, symbol: str, interval: str = "1h") -> pd.DataFrame:
        """Load OHLCV Parquet from local storage."""
        path = PROCESSED_DIR / f"{symbol.lower()}_{interval}_ohlcv.parquet"
        if not path.exists():
            logger.warning(f"[Loader] No OHLCV data for {symbol}. Run ETL pipeline first.")
            return pd.DataFrame()
        df = pd.read_parquet(path)
        logger.info(f"[Loader] Loaded OHLCV for {symbol}: {len(df)} rows")
        return df

    def load_features(self, symbol: str) -> pd.DataFrame:
        """Load features Parquet from local storage."""
        path = FEATURES_DIR / f"{symbol.lower()}_features.parquet"
        if not path.exists():
            logger.warning(f"[Loader] No features for {symbol}. Run feature pipeline first.")
            return pd.DataFrame()
        return pd.read_parquet(path)

    def load_latest_ticker(self, symbol: str) -> dict | None:
        """Return latest ticker row for a symbol."""
        path = PROCESSED_DIR / f"{symbol.lower()}_tickers.csv"
        if not path.exists():
            return None
        df = pd.read_csv(path)
        if df.empty:
            return None
        return df.iloc[-1].to_dict()

    def list_available_symbols(self) -> list[str]:
        """Return list of symbols with processed OHLCV data."""
        files = list(PROCESSED_DIR.glob("*_1h_ohlcv.parquet"))
        return [f.stem.split("_")[0].upper() for f in files]


# Singleton for use across pipeline scripts
loader = LocalLoader()
