"""
Market Charts Page
==================
Candlestick chart + RSI + MACD + Bollinger Bands
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from pipelines.ingestion.binance_client import BinanceClient, ingest_klines
from pipelines.transformation.cleaner import parse_klines
from pipelines.transformation.features import build_features
from pipelines.loaders.local_loader import loader
from dashboard.streamlit_app.components.charts import (
    candlestick_chart, rsi_chart, macd_chart, bollinger_chart
)
from dashboard.streamlit_app.components.metrics import page_header

st.set_page_config(page_title="Cryptrix — Market Charts", layout="wide", page_icon="📊")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0a0f1e; color: #f1f5f9; }
    .stSidebar { background-color: #0d1525; border-right: 1px solid #1e2d45; }
    .block-container { padding: 1.5rem 2rem; }
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=120_000, key="market_refresh")

# Sidebar controls
with st.sidebar:
    st.markdown("## ⚙️ Chart Settings")
    symbol = st.selectbox("Symbol", ["BTC", "ETH", "SOL"], index=0)
    interval = st.selectbox("Interval", ["1h", "4h", "1d"], index=0)
    limit = st.slider("Candles", min_value=50, max_value=500, value=200, step=50)
    show_volume = st.toggle("Show Volume", value=True)
    st.divider()
    fetch_live = st.button("🔄 Fetch Live Data Now", use_container_width=True)

page_header(f"📊 {symbol} / USDT — Technical Analysis", f"Interval: {interval} · Last {limit} candles")

BINANCE_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}


@st.cache_data(ttl=110, show_spinner=False)
def load_chart_data(symbol: str, interval: str, limit: int):
    """Load OHLCV data — from local cache or live Binance."""
    # Try local first
    df = loader.load_ohlcv(symbol, interval=interval)
    if not df.empty and len(df) >= 20:
        return df.tail(limit)

    # Fetch live
    try:
        raw = ingest_klines(BINANCE_MAP[symbol], interval=interval, limit=limit, save=True)
        df = parse_klines(raw)
        df_features = build_features(df, add_target=False)
        loader.save_ohlcv(df, symbol, interval=interval)
        return df_features.tail(limit)
    except Exception as e:
        st.error(f"Could not fetch data: {e}")
        return None


if fetch_live:
    st.cache_data.clear()

with st.spinner(f"Loading {symbol} {interval} data..."):
    df = load_chart_data(symbol, interval, limit)

if df is None or df.empty:
    st.warning(
        "No data available. Make sure you can reach the Binance API, "
        "or run the ETL pipeline: `python pipelines/ingestion/binance_client.py`"
    )
    st.stop()

# Build features if not present
feature_cols = ["rsi", "macd_line", "bb_upper"]
if not all(c in df.columns for c in feature_cols):
    df = build_features(df, add_target=False)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
st.plotly_chart(candlestick_chart(df, symbol, show_volume=show_volume), use_container_width=True)

col_rsi, col_macd = st.columns(2)
with col_rsi:
    st.plotly_chart(rsi_chart(df, symbol), use_container_width=True)
with col_macd:
    st.plotly_chart(macd_chart(df, symbol), use_container_width=True)

st.plotly_chart(bollinger_chart(df, symbol), use_container_width=True)

# ---------------------------------------------------------------------------
# Latest Stats Table
# ---------------------------------------------------------------------------
with st.expander("📋 Latest Data Table", expanded=False):
    display_cols = [c for c in ["timestamp","open","high","low","close","volume","rsi","macd_line","bb_width","atr"] if c in df.columns]
    st.dataframe(
        df[display_cols].tail(20).sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
