from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.websocket import ws_manager
from app.models.schemas import DBPredictionResult, PredictionResponse, PredictionBase
from app.utils.logger import logger

router = APIRouter()

@router.get("/predictions", response_model=List[PredictionResponse])
async def get_latest_predictions(db: AsyncSession = Depends(get_db)):
    """
    Retrieves the latest AI ML predictions from PostgreSQL.
    """
    result = await db.execute(
        select(DBPredictionResult)
        .order_by(DBPredictionResult.timestamp.desc())
        .limit(20)
    )
    predictions = result.scalars().all()
    return predictions

@router.post("/predict", response_model=PredictionResponse)
async def publish_prediction(prediction_in: PredictionBase, db: AsyncSession = Depends(get_db)):
    """
    Registers a new ML prediction (invoked by ML training/inference tasks) and broadcasts in real-time.
    """
    db_pred = DBPredictionResult(
        symbol=prediction_in.symbol,
        current_price=prediction_in.current_price,
        predicted_price=prediction_in.predicted_price,
        direction=prediction_in.direction,
        confidence=prediction_in.confidence,
        model_name=prediction_in.model_name,
        horizon=prediction_in.horizon
    )
    db.add(db_pred)
    await db.flush()
    
    pred_data = PredictionResponse.from_attributes(db_pred)
    
    # Broadcast predictions to frontend dashboard
    await ws_manager.broadcast_global({
        "type": "prediction",
        "data": pred_data.model_dump(mode="json")
    })
    
    logger.info(f"Registered prediction: {prediction_in.symbol} -> Direction: {prediction_in.direction}")
    return pred_data
