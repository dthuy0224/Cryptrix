"""
FastAPI Main Application
=========================
Entry point for the Cryptrix Prediction API.

Endpoints:
  GET  /health
  GET  /api/v1/market/tickers
  GET  /api/v1/market/ticker/{symbol}
  GET  /api/v1/market/history/{symbol}
  GET  /api/v1/market/indicators/{symbol}
  GET  /api/v1/predict/{symbol}
  GET  /api/v1/predict/batch
  GET  /api/v1/sentiment/{symbol}
  GET  /api/v1/sentiment/all
  POST /api/v1/sentiment

Docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.fastapi_service.config import settings
from api.fastapi_service.routers import market, predictions, sentiment
from api.fastapi_service.schemas.models import HealthResponse
from pipelines.loaders.local_loader import loader
from utils import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.PROJECT_NAME} API v{settings.VERSION} [{settings.ENVIRONMENT}]")
    available_symbols = loader.list_available_symbols()
    logger.info(f"Available data symbols: {available_symbols or 'None — run ETL pipeline first'}")
    yield
    logger.info("Shutting down Cryptrix API.")


app = FastAPI(
    title=f"{settings.PROJECT_NAME} — Crypto Intelligence API",
    description=(
        "End-to-end crypto analytics and AI prediction platform. "
        "Provides realtime market data, technical indicators, ML predictions, and social sentiment."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(market.router, prefix=settings.API_PREFIX)
app.include_router(predictions.router, prefix=settings.API_PREFIX)
app.include_router(sentiment.router, prefix=settings.API_PREFIX)


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health probe for load balancers and Kubernetes."""
    available_symbols = loader.list_available_symbols()
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        data_available={sym: True for sym in available_symbols},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.fastapi_service.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
