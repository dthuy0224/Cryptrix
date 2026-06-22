"""
Sentiment Router
================
GET  /api/v1/sentiment/{symbol}  — Latest sentiment for a symbol
GET  /api/v1/sentiment/all       — Sentiment for all tracked symbols
POST /api/v1/sentiment           — Ingest new sentiment record (from Airflow DAG)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from api.fastapi_service.schemas.models import SentimentRequest, SentimentResponse
from pipelines.ingestion.sentiment_client import SentimentClient
from utils import logger

router = APIRouter(prefix="/sentiment", tags=["Social Sentiment"])

TRACKED_SYMBOLS = ["BTC", "ETH", "SOL"]

# In-memory store (replace with Redis or DB in production)
_sentiment_store: dict[str, dict] = {}


@router.get("/all", response_model=list[SentimentResponse])
async def get_all_sentiment():
    """Return latest sentiment for all tracked symbols."""
    results = []
    client = SentimentClient()

    for symbol in TRACKED_SYMBOLS:
        if symbol in _sentiment_store:
            results.append(SentimentResponse(**_sentiment_store[symbol]))
        else:
            # Fetch fresh (uses mock if no API keys)
            data = client.get_combined_sentiment(symbol)
            record = {
                "symbol": data["symbol"],
                "sentiment_score": data["score"],
                "sentiment_label": data["label"],
                "mention_count": data["mention_count"],
                "source_breakdown": data.get("source_breakdown", {}),
                "timestamp": data["timestamp"],
            }
            _sentiment_store[symbol] = record
            results.append(SentimentResponse(**record))

    return results


@router.get("/{symbol}", response_model=SentimentResponse)
async def get_sentiment(symbol: str):
    """Return latest sentiment score for a specific symbol."""
    symbol = symbol.upper()
    if symbol not in TRACKED_SYMBOLS:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not tracked.")

    if symbol in _sentiment_store:
        return SentimentResponse(**_sentiment_store[symbol])

    client = SentimentClient()
    data = client.get_combined_sentiment(symbol)
    record = {
        "symbol": data["symbol"],
        "sentiment_score": data["score"],
        "sentiment_label": data["label"],
        "mention_count": data["mention_count"],
        "source_breakdown": data.get("source_breakdown", {}),
        "timestamp": data["timestamp"],
    }
    _sentiment_store[symbol] = record
    return SentimentResponse(**record)


@router.post("", response_model=SentimentResponse, status_code=201)
async def ingest_sentiment(payload: SentimentRequest):
    """
    Ingest a new sentiment record from Airflow DAG or external service.
    Stores in memory and returns the stored record.
    """
    record = payload.model_dump()
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    _sentiment_store[payload.symbol.upper()] = record
    logger.info(f"[API] Sentiment ingested for {payload.symbol}: {payload.sentiment_score:.3f}")
    return SentimentResponse(**record)
