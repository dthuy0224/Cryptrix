"""
Pydantic v2 Schemas (API Data Contracts)
=========================================
All response models use model_validate() — NOT from_attributes() (Pydantic v1 only).
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

class TickerResponse(BaseModel):
    symbol: str
    price: float
    change_24h_pct: float
    change_24h_abs: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: str

    model_config = {"from_attributes": True}


class OHLCVRecord(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketHistoryResponse(BaseModel):
    symbol: str
    interval: str
    records: list[OHLCVRecord]
    total: int


# ---------------------------------------------------------------------------
# Technical Indicators
# ---------------------------------------------------------------------------

class IndicatorsResponse(BaseModel):
    symbol: str
    timestamp: str
    close: float
    rsi: float
    macd_line: float
    macd_signal: float
    macd_hist: float
    sma_7: float
    sma_14: float
    sma_30: float
    bb_upper: float
    bb_lower: float
    bb_middle: float
    atr: float


# ---------------------------------------------------------------------------
# AI Predictions
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    symbol: str
    current_price: float
    predicted_price: float
    direction: str = Field(..., pattern="^(bullish|bearish|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_name: str
    horizon: str
    timestamp: str
    features_used: Optional[int] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------

class SentimentRequest(BaseModel):
    symbol: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    mention_count: int = Field(..., ge=0)
    source_breakdown: dict[str, int] = Field(default_factory=dict)


class SentimentResponse(SentimentRequest):
    timestamp: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    environment: str
    service: str
    version: str
    data_available: dict[str, bool]
