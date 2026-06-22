"""
AI Predictions Page
====================
Shows XGBoost model prediction results for all tracked symbols.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from streamlit_autorefresh import st_autorefresh

from models.inference.predict import engine
from pipelines.loaders.local_loader import loader
from dashboard.streamlit_app.components.metrics import render_prediction_card, page_header
from dashboard.streamlit_app.components.charts import COLORS, LAYOUT_BASE

st.set_page_config(page_title="Cryptrix — AI Predictions", layout="wide", page_icon="🤖")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0a0f1e; color: #f1f5f9; }
    .stSidebar { background-color: #0d1525; border-right: 1px solid #1e2d45; }
    .block-container { padding: 1.5rem 2rem; }
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=180_000, key="pred_refresh")

TRACKED = ["BTC", "ETH", "SOL"]

page_header("🤖 AI Market Direction Predictions", "XGBoost classifier · 24h horizon · Updated every 3 minutes")

# ---------------------------------------------------------------------------
# Fetch Predictions
# ---------------------------------------------------------------------------
@st.cache_data(ttl=170, show_spinner=False)
def get_predictions():
    return engine.predict_batch(TRACKED)


with st.spinner("Running inference..."):
    predictions = get_predictions()

if not predictions:
    st.error("No predictions available. Ensure feature data exists by running the ETL pipeline.")
    st.stop()

# ---------------------------------------------------------------------------
# Cards row
# ---------------------------------------------------------------------------
cols = st.columns(len(predictions))
for i, pred in enumerate(predictions):
    with cols[i]:
        render_prediction_card(pred)

st.divider()

# ---------------------------------------------------------------------------
# Confidence gauge chart
# ---------------------------------------------------------------------------
col_conf, col_detail = st.columns([1, 1.2])

with col_conf:
    st.markdown("### Confidence Scores")
    fig = go.Figure()
    for pred in predictions:
        direction = pred["direction"]
        color = COLORS["bullish"] if direction == "bullish" else COLORS["bearish"]
        fig.add_trace(go.Bar(
            x=[pred["confidence"] * 100],
            y=[pred["symbol"]],
            orientation="h",
            marker_color=color,
            text=[f"{pred['confidence']*100:.0f}% {direction.upper()}"],
            textposition="inside",
            insidetextanchor="middle",
            name=pred["symbol"],
        ))
    fig.update_layout(
        **LAYOUT_BASE,
        height=200,
        xaxis=dict(range=[0, 100], title="Confidence %", gridcolor=COLORS["border"]),
        showlegend=False,
        barmode="group",
        title=dict(text="Model Confidence by Symbol", font=dict(size=13)),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_detail:
    st.markdown("### Price Targets")
    data = []
    for pred in predictions:
        if pred.get("current_price", 0) > 0:
            change = ((pred["predicted_price"] - pred["current_price"]) / pred["current_price"]) * 100
        else:
            change = 0.0
        data.append({
            "Symbol": pred["symbol"],
            "Current Price": f"${pred['current_price']:,.2f}",
            "Predicted Price": f"${pred['predicted_price']:,.2f}",
            "Expected Δ": f"{change:+.2f}%",
            "Direction": pred["direction"].upper(),
            "Confidence": f"{pred['confidence']:.1%}",
            "Model": pred["model_name"],
            "Horizon": pred["horizon"],
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Feature Importance (lazy-import xgboost — only if model file exists)
# ---------------------------------------------------------------------------
st.markdown("### 📈 Feature Importance (Latest Model)")
FEATURE_COLS = [
    "close", "volume", "sma_7", "sma_14", "sma_30",
    "ema_9", "ema_21", "rsi",
    "macd_line", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width",
    "atr", "obv",
]

sym_for_fi = st.selectbox("Symbol", TRACKED, index=0, key="fi_sym")
local_model = Path(f"models/saved_models/{sym_for_fi.lower()}_xgb.json")

if local_model.exists():
    try:
        import xgboost as xgb  # lazy import — only when model exists
        model = xgb.XGBClassifier()
        model.load_model(local_model)
        importance = model.feature_importances_

        fig_fi = go.Figure(go.Bar(
            x=importance,
            y=FEATURE_COLS,
            orientation="h",
            marker=dict(
                color=importance,
                colorscale=[[0, COLORS["surface"]], [0.5, COLORS["accent"]], [1, COLORS["accent2"]]],
                showscale=False,
            ),
        ))
        fig_fi.update_layout(
            **LAYOUT_BASE,
            height=420,
            title=dict(text=f"{sym_for_fi} XGBoost Feature Importance", font=dict(size=13)),
            xaxis=dict(title="Importance Score", gridcolor=COLORS["border"]),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_fi, use_container_width=True)
    except ImportError:
        st.warning("XGBoost not installed. Run: `pip install xgboost`")
else:
    st.info(
        f"No trained model found for {sym_for_fi}. "
        "Run: `python models/training/xgboost_trainer.py --symbol BTC`"
    )
