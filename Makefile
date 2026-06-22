.PHONY: help up down logs install dev-api dev-dashboard etl train clean

# ==============================================================================
# Cryptrix — Developer Shortcuts
# ==============================================================================

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --- Docker Commands ---

up:  ## Start all Docker services
	docker compose up -d
	@echo "✅ Services started:"
	@echo "   Dashboard  → http://localhost:8501"
	@echo "   API        → http://localhost:8000/docs"
	@echo "   MLflow     → http://localhost:5000"

down:  ## Stop all Docker services
	docker compose down

restart:  ## Restart all services
	docker compose restart

logs:  ## Tail all service logs
	docker compose logs -f

logs-api:  ## Tail API logs
	docker compose logs -f api

logs-dashboard:  ## Tail Dashboard logs
	docker compose logs -f dashboard

build:  ## Rebuild Docker images
	docker compose build --no-cache

# --- Local Development ---

install:  ## Install Python dependencies (creates .venv)
	pip install -e ".[dev]" 2>/dev/null || pip install \
	  httpx requests pandas numpy xgboost scikit-learn mlflow \
	  fastapi uvicorn pydantic pydantic-settings loguru streamlit \
	  plotly streamlit-autorefresh pyarrow loguru python-dotenv \
	  prophet great-expectations pytest ruff

dev-api:  ## Run FastAPI in development mode (hot reload)
	uvicorn api.fastapi_service.main:app --reload --host 0.0.0.0 --port 8000

dev-dashboard:  ## Run Streamlit dashboard locally
	streamlit run dashboard/streamlit_app/app.py

# --- Data Pipeline ---

etl-run:  ## Run full ETL pipeline locally (fetch + clean + features)
	@echo "🔄 Running ETL for BTC, ETH, SOL..."
	python -c " \
	from pipelines.ingestion.binance_client import ingest_klines, ingest_ticker; \
	from pipelines.transformation.cleaner import parse_klines; \
	from pipelines.transformation.features import build_features; \
	from pipelines.loaders.local_loader import loader; \
	symbols = [('BTC','BTCUSDT'),('ETH','ETHUSDT'),('SOL','SOLUSDT')]; \
	[loader.save_ohlcv(build_features(parse_klines(ingest_klines(bs, limit=500))), s) for s,bs in symbols]; \
	print('✅ ETL complete')"

# --- ML Training ---

train-xgb:  ## Train XGBoost for all symbols
	python models/training/xgboost_trainer.py --symbol BTC
	python models/training/xgboost_trainer.py --symbol ETH
	python models/training/xgboost_trainer.py --symbol SOL

train-prophet:  ## Train Prophet for all symbols
	python models/training/prophet_trainer.py --symbol BTC
	python models/training/prophet_trainer.py --symbol ETH

predict:  ## Run inference and print predictions
	python models/inference/predict.py

# --- Code Quality ---

lint:  ## Run ruff linter
	ruff check . --fix

format:  ## Format code with ruff
	ruff format .

test:  ## Run test suite
	pytest tests/ -v

# --- Utilities ---

clean:  ## Clean Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true

clean-data:  ## Remove all local data files (keeps directories)
	find data/ -name "*.json" -delete
	find data/ -name "*.csv" -delete
	find data/ -name "*.parquet" -delete
	@echo "🗑️ Data files cleared."

clean-models:  ## Remove local saved model files
	find models/saved_models/ -name "*.json" -delete
	find models/saved_models/ -name "*.csv" -delete
	@echo "🗑️ Saved models cleared."

status:  ## Show Docker service status
	docker compose ps
