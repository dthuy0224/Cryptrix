"""
Social Sentiment Page
======================
NLP-based sentiment scores from Reddit, Twitter/X, and news sources.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

from pipelines.ingestion.sentiment_client import SentimentClient
from dashboard.streamlit_app.components.metrics import render_sentiment_badge, page_header
from dashboard.streamlit_app.components.charts import sentiment_gauge, COLORS, LAYOUT_BASE
import plotly.graph_objects as go

st.set_page_config(page_title="Cryptrix — Social Sentiment", layout="wide", page_icon="💬")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0a0f1e; color: #f1f5f9; }
    .stSidebar { background-color: #0d1525; border-right: 1px solid #1e2d45; }
    .block-container { padding: 1.5rem 2rem; }
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=300_000, key="sentiment_refresh")

TRACKED = ["BTC", "ETH", "SOL"]

page_header(
    "💬 Social Sentiment Intelligence",
    "NLP analysis from Reddit · Twitter/X · News feeds · Updated every 5 minutes"
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data(ttl=290, show_spinner=False)
def get_sentiments():
    client = SentimentClient(
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        news_api_key=os.getenv("NEWS_API_KEY"),
    )
    return [client.get_combined_sentiment(sym) for sym in TRACKED]


with st.spinner("Analyzing community signals..."):
    sentiments = get_sentiments()

# ---------------------------------------------------------------------------
# Gauge row
# ---------------------------------------------------------------------------
st.markdown("### Sentiment Gauges")
gauge_cols = st.columns(len(sentiments))
for i, sent in enumerate(sentiments):
    with gauge_cols[i]:
        fig = sentiment_gauge(sent["score"], sent["symbol"])
        st.plotly_chart(fig, use_container_width=True)
        label = sent["label"]
        color = "#10b981" if label == "positive" else "#f43f5e" if label == "negative" else "#94a3b8"
        st.markdown(
            f"<p style='text-align:center;color:{color};font-weight:700;font-size:0.85rem;margin-top:-10px;'>"
            f"{label.upper()} · {sent['mention_count']:,} mentions</p>",
            unsafe_allow_html=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# Source breakdown bar chart
# ---------------------------------------------------------------------------
col_breakdown, col_table = st.columns([1.3, 0.7])

with col_breakdown:
    st.markdown("### Source Breakdown")
    symbols = [s["symbol"] for s in sentiments]
    reddit_counts = [s.get("source_breakdown", {}).get("reddit", 0) for s in sentiments]
    news_counts = [s.get("source_breakdown", {}).get("news", 0) for s in sentiments]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Reddit", x=symbols, y=reddit_counts,
                          marker_color=COLORS["accent"], opacity=0.85))
    fig.add_trace(go.Bar(name="News", x=symbols, y=news_counts,
                          marker_color=COLORS["gold"], opacity=0.85))
    fig.update_layout(
        **LAYOUT_BASE,
        barmode="group",
        height=280,
        title=dict(text="Mentions by Source", font=dict(size=13)),
        yaxis=dict(title="Mention Count", gridcolor=COLORS["border"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("### Summary Table")
    data = []
    for s in sentiments:
        data.append({
            "Symbol": s["symbol"],
            "Score": f"{s['score']:+.3f}",
            "Label": s["label"].upper(),
            "Mentions": f"{s['mention_count']:,}",
            "Reddit": f"{s.get('source_breakdown', {}).get('reddit', 0):,}",
            "News": f"{s.get('source_breakdown', {}).get('news', 0):,}",
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------------
# Sentiment vs Price score comparison
# ---------------------------------------------------------------------------
st.markdown("### Sentiment Scores Comparison")
fig2 = go.Figure()
for s in sentiments:
    score = s["score"]
    color = COLORS["bullish"] if score > 0.15 else COLORS["bearish"] if score < -0.15 else COLORS["neutral"]
    fig2.add_trace(go.Bar(
        name=s["symbol"],
        x=[s["symbol"]],
        y=[score],
        marker_color=color,
        text=[f"{score:+.3f}"],
        textposition="outside",
    ))
fig2.add_hline(y=0.15, line_dash="dot", line_color=COLORS["bullish"], opacity=0.5, annotation_text="Positive threshold")
fig2.add_hline(y=-0.15, line_dash="dot", line_color=COLORS["bearish"], opacity=0.5, annotation_text="Negative threshold")
fig2.update_layout(
    **LAYOUT_BASE,
    height=280,
    yaxis=dict(range=[-1, 1], title="Sentiment Score", gridcolor=COLORS["border"]),
    title=dict(text="Community Sentiment Score by Symbol (-1 to +1)", font=dict(size=13)),
    showlegend=False,
)
st.plotly_chart(fig2, use_container_width=True)

# Note about real API integration
with st.expander("ℹ️ About Sentiment Data Sources"):
    st.markdown("""
    Currently running with **mock sentiment data** (realistic random scores with bullish bias).
    
    To enable **real sentiment analysis**, configure in `.env`:
    ```
    REDDIT_CLIENT_ID=your_id
    REDDIT_CLIENT_SECRET=your_secret  
    NEWS_API_KEY=your_key
    ```
    
    **Production pipeline** will use **FinBERT** (Financial BERT) for accurate NLP sentiment scoring,
    as recommended in the project Blueprint.
    """)
