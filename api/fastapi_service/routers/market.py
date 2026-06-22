"""
Market Data Router
==================
GET /api/v1/market/tickers    — Latest 24h ticker for all tracked symbols
GET /api/v1/market/ticker/{symbol}  — Single symbol ticker
GET /api/v1/market/history/{symbol} — OHLCV history
GET /api/v1/market/indicators/{symbol} — Latest technical indicators
"""
from fastapi import APIRouter, HTTPException
from api.fastapi_service.schemas.models import (
    TickerResponse, MarketHistoryResponse, OHLCVRecord, IndicatorsResponse
)
from pipelines.ingestion.binance_client import BinanceClient
from pipelines.transformation.cleaner import parse_ticker_24h
from pipelines.loaders.local_loader import loader
from utils import logger

router = APIRouter(prefix="/market", tags=["Market Data"])

TRACKED_SYMBOLS = ["BTC", "ETH", "SOL"]
BINANCE_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}


@router.get("/tickers", response_model=list[TickerResponse])
async def get_all_tickers():
    """
    Fetch live 24h ticker data from Binance for all tracked symbols.
    Falls back to locally cached data if API is unreachable.
    """
    client = BinanceClient()
    results = []

    for symbol in TRACKED_SYMBOLS:
        binance_symbol = BINANCE_MAP[symbol]
        try:
            raw = client.get_ticker_24h(binance_symbol)
            clean = parse_ticker_24h(raw, symbol=symbol)
            results.append(TickerResponse(**clean))
        except Exception as e:
            logger.warning(f"[API] Failed to fetch live ticker for {symbol}: {e}")
            # Fallback to cached
            cached = loader.load_latest_ticker(symbol)
            if cached:
                results.append(TickerResponse(**cached))

    if not results:
        raise HTTPException(status_code=503, detail="No market data available.")

    return results


@router.get("/ticker/{symbol}", response_model=TickerResponse)
async def get_ticker(symbol: str):
    """Fetch live 24h ticker for a specific symbol (e.g., BTC, ETH, SOL)."""
    symbol = symbol.upper()
    if symbol not in BINANCE_MAP:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not tracked.")

    client = BinanceClient()
    try:
        raw = client.get_ticker_24h(BINANCE_MAP[symbol])
        clean = parse_ticker_24h(raw, symbol=symbol)
        return TickerResponse(**clean)
    except Exception as e:
        logger.error(f"[API] Binance error for {symbol}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch ticker for {symbol}.")


@router.get("/history/{symbol}", response_model=MarketHistoryResponse)
async def get_history(symbol: str, interval: str = "1h", limit: int = 100):
    """
    Return OHLCV history from local storage.
    Requires ETL pipeline to have run at least once.
    """
    symbol = symbol.upper()
    df = loader.load_ohlcv(symbol, interval=interval)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data for {symbol}. Run: airflow trigger_dag cryptrix_market_etl"
        )

    df_tail = df.tail(limit)
    records = [
        OHLCVRecord(
            timestamp=str(row["timestamp"]),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"],
        )
        for _, row in df_tail.iterrows()
    ]

    return MarketHistoryResponse(
        symbol=symbol,
        interval=interval,
        records=records,
        total=len(records),
    )


@router.get("/indicators/{symbol}", response_model=IndicatorsResponse)
async def get_indicators(symbol: str):
    """Return latest technical indicators for a symbol."""
    symbol = symbol.upper()
    df = loader.load_features(symbol)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No feature data for {symbol}.")

    latest = df.iloc[-1]

    def safe_float(val, default: float = 0.0) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    return IndicatorsResponse(
        symbol=symbol,
        timestamp=str(latest.get("timestamp", "")),
        close=safe_float(latest.get("close")),
        rsi=safe_float(latest.get("rsi")),
        macd_line=safe_float(latest.get("macd_line")),
        macd_signal=safe_float(latest.get("macd_signal")),
        macd_hist=safe_float(latest.get("macd_hist")),
        sma_7=safe_float(latest.get("sma_7")),
        sma_14=safe_float(latest.get("sma_14")),
        sma_30=safe_float(latest.get("sma_30")),
        bb_upper=safe_float(latest.get("bb_upper")),
        bb_lower=safe_float(latest.get("bb_lower")),
        bb_middle=safe_float(latest.get("bb_middle")),
        atr=safe_float(latest.get("atr")),
    )
