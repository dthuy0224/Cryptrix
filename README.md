# Cryptrix — Crypto AI Platform

> End-to-end crypto analytics and AI prediction platform following the **Crypto AI Platform Blueprint**.

## 🏗️ Architecture

```
Data Sources → Ingestion Layer → Storage Layer → Serving Layer → AI/ML Layer
```

```
Cryptrix/
├── airflow/dags/          # Orchestration (Hourly ETL · Sentiment · Weekly Retrain)
├── pipelines/
│   ├── ingestion/         # Binance · CoinGecko · Sentiment APIs
│   ├── transformation/    # Cleaner · Feature Engineering (RSI/MACD/BB)
│   └── loaders/           # Local storage (GCS/BigQuery interface)
├── models/
│   ├── training/          # XGBoost Classifier · Prophet Forecaster
│   └── inference/         # Unified prediction engine
├── api/fastapi_service/   # FastAPI REST API
├── dashboard/             # Streamlit Analytics Dashboard
├── data/                  # Local data lake (raw / processed / features)
├── docker/                # Dockerfiles
└── docker-compose.yml
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start Infrastructure
```bash
make up
# Dashboard  → http://localhost:8501
# API Docs   → http://localhost:8000/docs
# MLflow     → http://localhost:5000
```

### 3. Run ETL Pipeline (fetch data)
```bash
make etl-run
```

### 4. Train ML Models
```bash
make train-xgb
make train-prophet   # Optional
```

### 5. View Dashboard
Open http://localhost:8501

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | Apache Airflow |
| Data Processing | Pandas, NumPy |
| Feature Engineering | RSI, MACD, Bollinger Bands, ATR, OBV |
| ML Models | XGBoost (classification) · Prophet (forecasting) |
| MLOps | MLflow |
| API | FastAPI + Pydantic v2 |
| Dashboard | Streamlit + Plotly |
| Database | PostgreSQL |
| Cache | Redis |
| Deployment | Docker Compose |

## 📊 Data Sources

- **Binance API** — OHLCV klines, 24h ticker stats
- **CoinGecko API** — Market cap, rankings
- **Reddit/News APIs** — Social sentiment (mock fallback if no API key)

## 🤖 ML Models

| Model | Purpose | Status |
|-------|---------|--------|
| XGBoost Classifier | Market direction (bullish/bearish) | ✅ |
| Prophet Forecaster | Hourly price time-series | ✅ |
| LSTM | Sequential deep learning | 🔜 Phase 5 |
| FinBERT | NLP sentiment scoring | 🔜 Phase 5 |

## 📋 Development Roadmap

- [x] **Phase 1** — MVP: Binance data + Streamlit dashboard
- [x] **Phase 2** — Data Engineering: Airflow ETL + feature pipeline
- [x] **Phase 3** — AI Prediction: XGBoost + Prophet + FastAPI
- [x] **Phase 4** — Docker deployment
- [ ] **Phase 5** — Advanced: Kafka streaming + GCS/BigQuery + FinBERT

## ⚡ Developer Commands

```bash
make help          # List all commands
make dev-api       # Run FastAPI locally (hot reload)
make dev-dashboard # Run Streamlit locally
make etl-run       # Fetch & process data
make train-xgb     # Train XGBoost models
make lint          # Run ruff linter
make test          # Run test suite
make clean         # Clear Python cache
```
