"""
Predictions Router
==================
GET  /api/v1/predict/{symbol}   — Get ML prediction for a symbol
GET  /api/v1/predict/batch      — Predictions for all tracked symbols
POST /api/v1/predict/run/{symbol} — Trigger prediction and return result
"""
from fastapi import APIRouter, HTTPException
from api.fastapi_service.schemas.models import PredictionResponse
from models.inference.predict import engine
from utils import logger

router = APIRouter(prefix="/predict", tags=["AI Predictions"])

TRACKED_SYMBOLS = ["BTC", "ETH", "SOL"]


@router.get("/batch", response_model=list[PredictionResponse])
async def predict_batch():
    """Generate AI predictions for all tracked symbols."""
    try:
        results = engine.predict_batch(TRACKED_SYMBOLS)
        return [PredictionResponse(**r) for r in results]
    except Exception as e:
        logger.error(f"[API] Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}", response_model=PredictionResponse)
async def predict_symbol(symbol: str):
    """
    Generate AI market direction prediction for a specific symbol.
    
    Returns direction (bullish/bearish/neutral), confidence score,
    predicted price target, and model metadata.
    """
    symbol = symbol.upper()
    if symbol not in TRACKED_SYMBOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not supported. Available: {TRACKED_SYMBOLS}"
        )

    try:
        result = engine.predict(symbol)
        return PredictionResponse(**result)
    except Exception as e:
        logger.error(f"[API] Prediction error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
