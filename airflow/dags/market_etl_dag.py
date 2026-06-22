"""
Market ETL DAG — Hourly BTC/ETH/SOL Pipeline
=============================================
Airflow DAG: cryptrix_market_etl

Schedule: Every hour
Tasks:
  1. ingest_raw_klines     — Pull OHLCV from Binance → save to data/raw/binance/
  2. ingest_raw_tickers    — Pull 24h ticker stats → save to data/raw/binance/
  3. clean_and_transform   — Parse + clean → data/processed/
  4. engineer_features     — Compute indicators → data/features/
  5. validate_quality      — Run quality checks, fail DAG on critical issues
"""
from datetime import datetime, timedelta
import json
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
default_args = {
    "owner": "cryptrix_data_eng",
    "depends_on_past": False,
    "start_date": datetime(2026, 6, 1),
    "email": ["alerts@cryptrix.ai"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
KLINE_INTERVAL = "1h"
KLINE_LIMIT = 500

# ---------------------------------------------------------------------------
# Task Functions
# ---------------------------------------------------------------------------

def task_ingest_klines(**context) -> dict:
    """
    Ingest OHLCV klines from Binance for all tracked symbols.
    Saves raw JSON to data/raw/binance/ and pushes file paths via XCom.
    """
    from pipelines.ingestion.binance_client import BinanceClient
    from datetime import timezone

    client = BinanceClient()
    saved_paths = {}

    for symbol in SYMBOLS:
        klines = client.get_klines(symbol, interval=KLINE_INTERVAL, limit=KLINE_LIMIT)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H")
        path = client.save_raw(klines, f"klines_{symbol}_{KLINE_INTERVAL}_{ts}.json")
        saved_paths[symbol] = str(path)
        print(f"[ETL] Ingested {len(klines)} klines for {symbol} → {path}")

    context["task_instance"].xcom_push(key="kline_paths", value=saved_paths)
    return saved_paths


def task_ingest_tickers(**context) -> dict:
    """
    Ingest 24h ticker stats for all symbols.
    """
    from pipelines.ingestion.binance_client import BinanceClient
    from datetime import timezone

    client = BinanceClient()
    saved_paths = {}

    for symbol in SYMBOLS:
        ticker = client.get_ticker_24h(symbol)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = client.save_raw(ticker, f"ticker_{symbol}_{ts}.json")
        saved_paths[symbol] = str(path)
        print(f"[ETL] Ingested ticker for {symbol}: ${float(ticker['lastPrice']):,.2f}")

    context["task_instance"].xcom_push(key="ticker_paths", value=saved_paths)
    return saved_paths


def task_clean_and_transform(**context) -> dict:
    """
    Parse raw klines JSON → clean OHLCV DataFrame → save as Parquet.
    """
    from pipelines.transformation.cleaner import parse_klines, check_ohlcv_quality
    from pipelines.loaders.local_loader import loader

    kline_paths: dict = context["task_instance"].xcom_pull(
        task_ids="ingest_klines", key="kline_paths"
    )

    if not kline_paths:
        raise ValueError(
            "[ETL] task_clean_and_transform: No kline_paths received from upstream task. "
            "Did ingest_klines succeed?"
        )

    reports = {}
    for symbol, raw_path in kline_paths.items():
        with open(raw_path) as f:
            raw = json.load(f)

        df = parse_klines(raw)
        quality = check_ohlcv_quality(df)
        reports[symbol] = quality

        if quality["status"] == "empty":
            raise ValueError(f"[ETL] Empty OHLCV data for {symbol}!")

        # Use symbol without USDT suffix for storage
        clean_symbol = symbol.replace("USDT", "")
        loader.save_ohlcv(df, clean_symbol, interval=KLINE_INTERVAL)
        print(f"[ETL] Cleaned {len(df)} rows for {clean_symbol}")

    return reports


def task_engineer_features(**context):
    """
    Load clean OHLCV → compute all technical indicators → save features Parquet.
    """
    from pipelines.transformation.features import build_features
    from pipelines.loaders.local_loader import loader

    for symbol in ["BTC", "ETH", "SOL"]:
        df = loader.load_ohlcv(symbol, interval=KLINE_INTERVAL)
        if df.empty:
            print(f"[ETL] No OHLCV data for {symbol}, skipping features.")
            continue

        df_features = build_features(df, add_target=True)
        loader.save_features(df_features, symbol)
        print(f"[ETL] Features built for {symbol}: {len(df_features)} rows, {len(df_features.columns)} columns")


def task_validate_quality(**context):
    """
    Final quality gate: check feature files exist and have sufficient rows.
    Fails DAG if data quality is critically low.
    """
    from pipelines.loaders.local_loader import loader

    MIN_ROWS = 50  # Minimum rows required for reliable ML

    failures = []
    for symbol in ["BTC", "ETH", "SOL"]:
        df = loader.load_features(symbol)
        if df.empty or len(df) < MIN_ROWS:
            failures.append(f"{symbol}: only {len(df)} rows (min {MIN_ROWS} required)")
        else:
            print(f"[Validate] {symbol} ✓ — {len(df)} feature rows available")

    if failures:
        raise ValueError(f"[Validate] Quality gate FAILED:\n" + "\n".join(failures))

    print("[Validate] All symbols passed quality gate ✓")


# ---------------------------------------------------------------------------
# DAG Definition
# ---------------------------------------------------------------------------

with DAG(
    dag_id="cryptrix_market_etl",
    default_args=default_args,
    description="Hourly ETL: Binance OHLCV → Clean → Features → Validate",
    schedule_interval="@hourly",
    catchup=False,
    tags=["cryptrix", "market", "etl"],
) as dag:

    ingest_klines = PythonOperator(
        task_id="ingest_klines",
        python_callable=task_ingest_klines,
    )

    ingest_tickers = PythonOperator(
        task_id="ingest_tickers",
        python_callable=task_ingest_tickers,
    )

    clean_transform = PythonOperator(
        task_id="clean_and_transform",
        python_callable=task_clean_and_transform,
    )

    engineer_features = PythonOperator(
        task_id="engineer_features",
        python_callable=task_engineer_features,
    )

    validate = PythonOperator(
        task_id="validate_quality",
        python_callable=task_validate_quality,
    )

    # DAG dependency graph
    [ingest_klines, ingest_tickers] >> clean_transform >> engineer_features >> validate
