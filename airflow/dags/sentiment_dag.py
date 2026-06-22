"""
Social Sentiment DAG — Every 15 Minutes
========================================
Airflow DAG: cryptrix_sentiment_pipeline

Schedule: */15 * * * * (every 15 minutes)
Tasks:
  1. collect_sentiment   — Pull Reddit/News sentiment for BTC, ETH, SOL
  2. aggregate_scores    — Merge signals, compute weighted sentiment index
  3. store_sentiment     — Persist to data/processed/
  4. push_to_api         — POST to FastAPI serving layer (if running)
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "cryptrix_data_eng",
    "depends_on_past": False,
    "start_date": datetime(2026, 6, 1),
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

SYMBOLS = ["BTC", "ETH", "SOL"]
API_BASE_URL = "http://api:8000/api/v1"   # Docker service name, not localhost


# ---------------------------------------------------------------------------
# Task Functions
# ---------------------------------------------------------------------------

def task_collect_sentiment(**context):
    """
    Pull sentiment signals from Reddit and News APIs.
    Falls back to mock scores when API keys are missing.
    """
    import os
    from pipelines.ingestion.sentiment_client import SentimentClient

    client = SentimentClient(
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        news_api_key=os.getenv("NEWS_API_KEY"),
    )

    results = []
    for symbol in SYMBOLS:
        sentiment = client.get_combined_sentiment(symbol)
        results.append(sentiment)
        print(f"[Sentiment] {symbol}: {sentiment['score']:.3f} ({sentiment['label']})")

    context["task_instance"].xcom_push(key="sentiment_results", value=results)
    return results


def task_store_sentiment(**context):
    """
    Persist sentiment results to data/processed/ CSV.
    """
    from pipelines.loaders.local_loader import loader

    results = context["task_instance"].xcom_pull(
        task_ids="collect_sentiment", key="sentiment_results"
    )

    if not results:
        print("[Sentiment] No results to store.")
        return

    loader.save_sentiment(results)
    print(f"[Sentiment] Stored {len(results)} sentiment records.")


def task_push_to_api(**context):
    """
    POST sentiment data to FastAPI serving layer.
    Gracefully skips if API is unreachable (non-blocking).
    """
    import httpx

    results = context["task_instance"].xcom_pull(
        task_ids="collect_sentiment", key="sentiment_results"
    )

    for record in (results or []):
        payload = {
            "symbol": record["symbol"],
            "sentiment_score": record["score"],
            "sentiment_label": record["label"],
            "mention_count": record["mention_count"],
            "source_breakdown": record.get("source_breakdown", {}),
        }
        try:
            resp = httpx.post(f"{API_BASE_URL}/sentiment", json=payload, timeout=5.0)
            print(f"[Sentiment→API] {record['symbol']}: HTTP {resp.status_code}")
        except Exception as exc:
            # Non-critical: API may not be running during Airflow-only dev
            print(f"[Sentiment→API] Could not reach API: {exc} (non-fatal)")


# ---------------------------------------------------------------------------
# DAG Definition
# ---------------------------------------------------------------------------

with DAG(
    dag_id="cryptrix_sentiment_pipeline",
    default_args=default_args,
    description="Sentiment signals: Reddit + News → aggregate → store → push to API",
    schedule_interval="*/15 * * * *",
    catchup=False,
    tags=["cryptrix", "sentiment", "nlp"],
) as dag:

    collect = PythonOperator(
        task_id="collect_sentiment",
        python_callable=task_collect_sentiment,
    )

    store = PythonOperator(
        task_id="store_sentiment",
        python_callable=task_store_sentiment,
    )

    push_api = PythonOperator(
        task_id="push_to_api",
        python_callable=task_push_to_api,
    )

    collect >> store >> push_api
