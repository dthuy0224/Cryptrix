"""
Cryptrix — Streamlit Dashboard Main App
=========================================
Entry point. Run with: streamlit run dashboard/streamlit_app/app.py

Pages:
  - 🏠 Home (this file)    — Overview dashboard
  - 📊 pages/1_Market.py  — Candlestick + indicators
  - 🤖 pages/2_Predictions.py — AI prediction results
  - 💬 pages/3_Sentiment.py   — Social sentiment index
"""
import sys
import os

# Add project root to path so all modules resolve correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from pipelines.ingestion.binance_client import BinanceClient
from pipelines.transformation.cleaner import parse_ticker_24h
from pipelines.ingestion.sentiment_client import SentimentClient
from models.inference.predict import engine as prediction_engine
from pipelines.loaders.local_loader import loader

from dashboard.streamlit_app.components.metrics import (
    render_ticker_card, render_prediction_card,
    render_sentiment_badge, page_header,
)
from dashboard.streamlit_app.components.charts import prediction_confidence_chart


# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Cryptrix — Crypto AI Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #0a0f1e;
        color: #f1f5f9;
    }
    .stSidebar {
        background-color: #0d1525;
        border-right: 1px solid #1e2d45;
    }
    .block-container { padding: 1.5rem 2rem; }
    section[data-testid="stSidebar"] > div { padding: 1.5rem 1rem; }
    .stMetric { background: #0d1525; border: 1px solid #1e2d45; border-radius: 10px; padding: 12px; }
    hr { border-color: #1e2d45; }
    div[data-testid="stExpander"] { background: #0d1525; border: 1px solid #1e2d45; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Auto-refresh every 60 seconds
# ---------------------------------------------------------------------------
refresh_count = st_autorefresh(interval=60_000, key="main_autorefresh")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:1.5rem;">
            <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);
                        padding:8px; border-radius:10px; font-size:1.2rem;">📈</div>
            <div>
                <div style="font-size:1.1rem; font-weight:800; color:#f1f5f9;">CRYPTRIX</div>
                <div style="font-size:0.68rem; color:#6366f1; text-transform:uppercase; letter-spacing:0.08em;">
                    v0.1 · AI Platform
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Navigation")
    st.page_link("app.py", label="🏠 Overview Dashboard", icon=None)
    st.page_link("pages/1_Market.py", label="📊 Market Charts")
    st.page_link("pages/2_Predictions.py", label="🤖 AI Predictions")
    st.page_link("pages/3_Sentiment.py", label="💬 Social Sentiment")

    st.divider()
    st.markdown("### Settings")
    selected_symbols = st.multiselect(
        "Tracked Symbols",
        options=["BTC", "ETH", "SOL", "BNB", "XRP"],
        default=["BTC", "ETH", "SOL"],
    )
    auto_refresh = st.toggle("Auto Refresh (60s)", value=True)

    st.divider()
    st.caption(f"🔄 Refresh #{refresh_count} | Data from Binance API")
    st.caption("📦 Stack: Airflow · XGBoost · FastAPI · Streamlit")


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------
page_header(
    "Crypto AI Intelligence Dashboard",
    "Realtime market data · AI predictions · Social sentiment · Technical analysis",
)

# Status bar
available = loader.list_available_symbols()
data_status = "✅ Local data available" if available else "⚠️ No local data — fetching live"
col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    st.info(f"🗄️ {data_status}")
with col_s2:
    st.info(f"🎯 Tracking: {', '.join(selected_symbols)}")
with col_s3:
    st.info("🤖 Model: XGBoost-v2-Classifier")

st.divider()

# ---------------------------------------------------------------------------
# Fetch Live Data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=55)  # Cache for 55s (refresh every 60s)
def fetch_tickers(symbols: tuple) -> list[dict]:
    client = BinanceClient()
    tickers = []
    binance_map = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT", "BNB": "BNBUSDT", "XRP": "XRPUSDT"}
    for sym in symbols:
        if sym in binance_map:
            try:
                raw = client.get_ticker_24h(binance_map[sym])
                tickers.append(parse_ticker_24h(raw, sym))
            except Exception:
                cached = loader.load_latest_ticker(sym)
                if cached:
                    tickers.append(cached)
    return tickers


@st.cache_data(ttl=120)
def fetch_predictions(symbols: tuple) -> list[dict]:
    return prediction_engine.predict_batch(list(symbols))


@st.cache_data(ttl=300)
def fetch_sentiment(symbols: tuple) -> list[dict]:
    client = SentimentClient()
    return [client.get_combined_sentiment(sym) for sym in symbols]


with st.spinner("Fetching live market data..."):
    tickers = fetch_tickers(tuple(selected_symbols))
    predictions = fetch_predictions(tuple(selected_symbols))
    sentiments = fetch_sentiment(tuple(selected_symbols))

# ---------------------------------------------------------------------------
# Section 1: Market Tickers
# ---------------------------------------------------------------------------
st.markdown("## 💹 Live Market Tickers")
ticker_cols = st.columns(min(len(tickers), 3))
for i, ticker in enumerate(tickers):
    with ticker_cols[i % 3]:
        render_ticker_card(ticker)

st.divider()

# ---------------------------------------------------------------------------
# Section 2: AI Predictions + Sentiment
# ---------------------------------------------------------------------------
col_pred, col_sent = st.columns([1.2, 0.8])

with col_pred:
    st.markdown("## 🤖 AI Market Predictions")
    for pred in predictions:
        render_prediction_card(pred)

    if predictions:
        st.plotly_chart(
            prediction_confidence_chart(predictions),
            use_container_width=True,
        )

with col_sent:
    st.markdown("## 💬 Social Sentiment")
    for sent in sentiments:
        render_sentiment_badge({
            "symbol": sent["symbol"],
            "score": sent["score"],
            "label": sent["label"],
            "source_breakdown": sent.get("source_breakdown", {}),
        })

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Quick Stats
# ---------------------------------------------------------------------------
st.markdown("## 📊 Quick Statistics")
if tickers:
    stat_cols = st.columns(4)
    with stat_cols[0]:
        btc = next((t for t in tickers if t["symbol"] == "BTC"), None)
        if btc:
            st.metric("BTC Price", f"${btc['price']:,.0f}", f"{btc['change_24h_pct']:+.2f}%")
    with stat_cols[1]:
        eth = next((t for t in tickers if t["symbol"] == "ETH"), None)
        if eth:
            st.metric("ETH Price", f"${eth['price']:,.0f}", f"{eth['change_24h_pct']:+.2f}%")
    with stat_cols[2]:
        bullish_count = sum(1 for p in predictions if p.get("direction") == "bullish")
        st.metric("Bullish Signals", f"{bullish_count}/{len(predictions)}")
    with stat_cols[3]:
        avg_conf = sum(p.get("confidence", 0) for p in predictions) / max(len(predictions), 1)
        st.metric("Avg Confidence", f"{avg_conf:.1%}")

st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; color:#1e2d45; font-size:0.75rem;">
    Cryptrix AI Platform · Powered by Binance API · XGBoost · Apache Airflow · Streamlit
</div>
""", unsafe_allow_html=True)
