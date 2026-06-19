from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON
from app.core.database import Base

# ==============================================================================
# SQLAlchemy ORM Database Models (PostgreSQL Tables)
# ==============================================================================

class DBMarketTicker(Base):
    __tablename__ = "market_tickers"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    change_24h = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class DBPredictionResult(Base):
    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    current_price = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=False)
    direction = Column(String, nullable=False) # bullish | bearish | neutral
    confidence = Column(Float, nullable=False)
    model_name = Column(String, nullable=False)
    horizon = Column(String, default="24h")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ==============================================================================
# Pydantic Schemas (API Data Contracts & Validation)
# ==============================================================================

class MarketTickerBase(BaseModel):
    symbol: str = Field(..., examples=["BTC", "ETH"])
    price: float = Field(..., gt=0.0)
    change24h: Optional[float] = Field(None, alias="change_24h")
    volume24h: Optional[float] = Field(None, alias="volume_24h")

class MarketTickerCreate(MarketTickerBase):
    pass

class MarketTickerResponse(MarketTickerBase):
    timestamp: datetime

    class Config:
        populate_by_name = True
        from_attributes = True

class PredictionBase(BaseModel):
    symbol: str = Field(..., examples=["BTC"])
    current_price: float = Field(..., gt=0.0)
    predicted_price: float = Field(..., gt=0.0)
    direction: str = Field(..., pattern="^(bullish|bearish|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_name: str
    horizon: str = "24h"

class PredictionResponse(PredictionBase):
    timestamp: datetime

    class Config:
        from_attributes = True

class SentimentBase(BaseModel):
    symbol: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    mention_count: int = Field(..., ge=0)
    source_breakdown: Dict[str, int] = Field(default_factory=dict)

class SentimentResponse(SentimentBase):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
