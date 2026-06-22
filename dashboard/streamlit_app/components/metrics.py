"""
KPI Metric Card Components for Streamlit Dashboard.
"""
import streamlit as st


def render_ticker_card(ticker: dict):
    """Render a styled ticker metric card."""
    is_up = ticker.get("change_24h_pct", 0) >= 0
    arrow = "▲" if is_up else "▼"
    color = "#10b981" if is_up else "#f43f5e"
    sign = "+" if is_up else ""

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0d1525 0%, #111827 100%);
            border: 1px solid #1e2d45;
            border-radius: 12px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 0.5rem;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.05em;">
                        {ticker['symbol']} / USDT
                    </div>
                    <div style="font-size:1.7rem; font-weight:700; color:#f1f5f9; margin-top:4px;">
                        ${ticker.get('price', 0):,.2f}
                    </div>
                    <div style="font-size:0.8rem; color:{color}; margin-top:4px;">
                        {arrow} {sign}{ticker.get('change_24h_pct', 0):.2f}%
                    </div>
                </div>
                <div style="text-align:right; font-size:0.72rem; color:#64748b;">
                    <div>24h High: <span style="color:#94a3b8;">${ticker.get('high_24h', 0):,.2f}</span></div>
                    <div>24h Low: <span style="color:#94a3b8;">${ticker.get('low_24h', 0):,.2f}</span></div>
                    <div>Volume: <span style="color:#94a3b8;">${ticker.get('volume_24h', 0)/1e9:.2f}B</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prediction_card(pred: dict):
    """Render a prediction result card."""
    direction = pred.get("direction", "neutral")
    is_bull = direction == "bullish"
    color = "#10b981" if is_bull else "#f43f5e" if direction == "bearish" else "#94a3b8"
    icon = "📈" if is_bull else "📉" if direction == "bearish" else "➡️"
    confidence_pct = pred.get("confidence", 0) * 100

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0d1525 0%, #111827 100%);
            border: 1px solid #1e2d45;
            border-left: 3px solid {color};
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.5rem;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase;">{pred.get('symbol')} · {pred.get('horizon', '24h')}</div>
                    <div style="font-size:1.1rem; font-weight:700; color:{color}; margin-top:4px;">
                        {icon} {direction.upper()}
                    </div>
                    <div style="font-size:0.72rem; color:#64748b; margin-top:4px;">
                        {pred.get('model_name', '—')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.75rem; color:#64748b;">Target</div>
                    <div style="font-size:1.2rem; font-weight:700; color:#f1f5f9;">${pred.get('predicted_price', 0):,.2f}</div>
                    <div style="
                        display:inline-block;
                        background: rgba(99,102,241,0.15);
                        border-radius:6px;
                        padding: 2px 8px;
                        font-size:0.72rem;
                        color:#a5b4fc;
                        margin-top:4px;
                    ">
                        Conf: {confidence_pct:.0f}%
                    </div>
                </div>
            </div>
            <div style="margin-top:10px; background:#1e2d45; border-radius:6px; height:5px; overflow:hidden;">
                <div style="width:{confidence_pct:.0f}%; background:{color}; height:100%; border-radius:6px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sentiment_badge(sentiment: dict):
    """Render a compact sentiment badge."""
    score = sentiment.get("score", 0)
    label = sentiment.get("label", "neutral")
    symbol = sentiment.get("symbol", "")
    color = "#10b981" if label == "positive" else "#f43f5e" if label == "negative" else "#94a3b8"
    pct = int((score + 1) / 2 * 100)

    st.markdown(
        f"""
        <div style="
            background: #0d1525;
            border: 1px solid #1e2d45;
            border-radius: 10px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.4rem;
        ">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="font-weight:600; color:#f1f5f9; font-size:0.9rem;">{symbol}</div>
                <div style="
                    background: rgba(255,255,255,0.05);
                    border-radius:6px;
                    padding: 2px 8px;
                    font-size:0.72rem;
                    color:{color};
                    text-transform:uppercase;
                    font-weight:600;
                ">{label}</div>
            </div>
            <div style="font-size:1.2rem; color:{color}; font-weight:700; margin:4px 0;">{score:+.3f}</div>
            <div style="background:#1e2d45; border-radius:6px; height:4px;">
                <div style="width:{pct}%; background:{color}; height:100%; border-radius:6px;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.68rem; color:#64748b; margin-top:4px;">
                <span>Reddit: {sentiment.get('source_breakdown', {}).get('reddit', 0):,}</span>
                <span>News: {sentiment.get('source_breakdown', {}).get('news', 0):,}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    """Render a styled page header."""
    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem;">
            <h1 style="
                font-size: 1.7rem;
                font-weight: 800;
                color: #f1f5f9;
                margin: 0;
                background: linear-gradient(90deg, #6366f1, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            ">{title}</h1>
            {"<p style='color:#64748b; font-size:0.85rem; margin:4px 0 0 0;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )
