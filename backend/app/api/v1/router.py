from fastapi import APIRouter
from app.api.v1.endpoints import market, predict

api_router = APIRouter()

# Register sub-routes
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(predict.router, prefix="/ml", tags=["AI Predictions"])
