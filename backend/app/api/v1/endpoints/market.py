from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.websocket import ws_manager
from app.models.schemas import DBMarketTicker, MarketTickerResponse, MarketTickerCreate
from app.utils.logger import logger

router = APIRouter()

@router.get("/tickers", response_model=List[MarketTickerResponse])
async def get_latest_tickers(db: AsyncSession = Depends(get_db)):
    """
    Fetches the latest recorded cryptocurrency market tickers from PostgreSQL.
    """
    result = await db.execute(
        select(DBMarketTicker)
        .order_by(DBMarketTicker.timestamp.desc())
        .limit(20)
    )
    tickers = result.scalars().all()
    return tickers

@router.post("/ticker", response_model=MarketTickerResponse)
async def create_ticker(ticker_in: MarketTickerCreate, db: AsyncSession = Depends(get_db)):
    """
    Saves a new market ticker to PostgreSQL and broadcasts it in real-time to active WebSockets.
    """
    db_ticker = DBMarketTicker(
        symbol=ticker_in.symbol,
        price=ticker_in.price,
        change_24h=ticker_in.change24h,
        volume_24h=ticker_in.volume24h
    )
    db.add(db_ticker)
    await db.flush() # Flush to populate ID/timestamps
    
    ticker_data = MarketTickerResponse.from_attributes(db_ticker)
    
    # Broadcast to WebSocket subscribers
    await ws_manager.broadcast_global({
        "type": "ticker",
        "data": ticker_data.model_dump(by_alias=True, mode="json")
    })
    
    return ticker_data

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint accepting client connections and providing real-time data push.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and receive client messages (e.g. client subscriptions)
            data = await websocket.receive_json()
            if "subscribe" in data:
                channel = data["subscribe"]
                await ws_manager.subscribe(websocket, channel)
                await websocket.send_json({
                    "status": "success",
                    "message": f"Subscribed to real-time channel: {channel}"
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket encounter error: {e}")
        ws_manager.disconnect(websocket)
