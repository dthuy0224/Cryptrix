from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.database import Base, engine
from app.api.v1.router import api_router
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application initialization and cleanup routines.
    """
    logger.info("Starting up Cryptrix Realtime API Backend...")
    
    # Auto-initialize PostgreSQL schema schemas in local development/sandbox env
    if settings.ENVIRONMENT == "development":
        logger.info("Development environment detected. Auto-creating PostgreSQL schemas...")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to auto-create schemas on startup: {e}")
            
    yield
    
    logger.info("Shutting down Cryptrix Realtime API Backend...")
    # Close connections
    await engine.dispose()
    logger.info("PostgreSQL engine connection pool disposed.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Realtime Cryptrix Crypto Intelligence and AI Forecasting API Server",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bind versioned API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["System Telemetry"])
async def health_check():
    """
    High-frequency Kubernetes/LoadBalancer health-check probe.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "service": settings.PROJECT_NAME
    }
