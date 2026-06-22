"""
Reusable Plotly chart components for the Streamlit dashboard.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------
COLORS = {
    "bg": "#0a0f1e",
    "surface": "#0d1525",
    "border": "#1e2d45",
    "accent": "#6366f1",       # indigo
    "accent2": "#8b5cf6",      # violet
    "bullish": "#10b981",      # emerald
    "bearish": "#f43f5e",      # rose
    "neutral": "#94a3b8",      # slate
    "text": "#f1f5f9",
    "muted": "#64748b",
    "gold": "#f59e0b",
}

LAYOUT_BASE = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["surface"],
    font=dict(color=COLORS["text"], family="Inter, system-ui, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor=COLORS["border"], zeroline=False),
    yaxis=dict(gridcolor=COLORS["border"], zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"]),
)


def candlestick_chart(df: pd.DataFrame, symbol: str, show_volume: bool = True) -> go.Figure:
    """
    Full candlestick chart with optional volume subplot.
    Requires columns: timestamp, open, high, low, close, volume
    """
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25],
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol,
            increasing_line_color=COLORS["bullish"],
            decreasing_line_color=COLORS["bearish"],
            increasing_fillcolor=COLORS["bullish"],
            decreasing_fillcolor=COLORS["bearish"],
        ),
        row=1, col=1,
    )

    # Volume bars
    if show_volume:
        colors = [
            COLORS["bullish"] if c >= o else COLORS["bearish"]
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df["timestamp"],
                y=df["volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.6,
            ),
            row=2, col=1,
        )

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=f"{symbol} / USDT — Candlestick Chart", font=dict(size=16)),
        xaxis_rangeslider_visible=False,
        height=480,
    )
    return fig


def rsi_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """RSI line chart with overbought/oversold zones."""
    fig = go.Figure()

    fig.add_shape(type="rect", x0=df["timestamp"].iloc[0], x1=df["timestamp"].iloc[-1],
                  y0=70, y1=100, fillcolor="rgba(244,63,94,0.08)", line_width=0)
    fig.add_shape(type="rect", x0=df["timestamp"].iloc[0], x1=df["timestamp"].iloc[-1],
                  y0=0, y1=30, fillcolor="rgba(16,185,129,0.08)", line_width=0)

    fig.add_hline(y=70, line_dash="dot", line_color=COLORS["bearish"], opacity=0.5)
    fig.add_hline(y=30, line_dash="dot", line_color=COLORS["bullish"], opacity=0.5)
    fig.add_hline(y=50, line_dash="dot", line_color=COLORS["muted"], opacity=0.3)

    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["rsi"],
        name="RSI (14)",
        line=dict(color=COLORS["accent"], width=2),
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.05)",
    ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=f"{symbol} RSI (14)", font=dict(size=14)),
        yaxis=dict(range=[0, 100], gridcolor=COLORS["border"], zeroline=False),
        height=220,
    )
    return fig


def macd_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """MACD chart with signal line and histogram."""
    fig = make_subplots(rows=1, cols=1)

    hist_colors = [
        COLORS["bullish"] if v >= 0 else COLORS["bearish"]
        for v in df["macd_hist"]
    ]

    fig.add_trace(go.Bar(
        x=df["timestamp"], y=df["macd_hist"],
        name="Histogram",
        marker_color=hist_colors,
        opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["macd_line"],
        name="MACD",
        line=dict(color=COLORS["accent"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df["macd_signal"],
        name="Signal",
        line=dict(color=COLORS["gold"], width=1.5, dash="dot"),
    ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=f"{symbol} MACD (12,26,9)", font=dict(size=14)),
        height=220,
        barmode="relative",
    )
    return fig


def bollinger_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Price chart with Bollinger Bands overlay."""
    fig = go.Figure()

    # Band fill
    fig.add_trace(go.Scatter(
        x=pd.concat([df["timestamp"], df["timestamp"][::-1]]),
        y=pd.concat([df["bb_upper"], df["bb_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(99,102,241,0.07)",
        line=dict(color="rgba(99,102,241,0)"),
        name="BB Band",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_upper"],
                              name="Upper Band", line=dict(color=COLORS["accent"], width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_middle"],
                              name="Middle (SMA20)", line=dict(color=COLORS["neutral"], width=1.5)))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_lower"],
                              name="Lower Band", line=dict(color=COLORS["accent"], width=1, dash="dot")))
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["close"],
                              name="Close Price", line=dict(color=COLORS["bullish"], width=2)))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=f"{symbol} Bollinger Bands (20,2)", font=dict(size=14)),
        height=320,
    )
    return fig


def sentiment_gauge(score: float, symbol: str) -> go.Figure:
    """Gauge chart for sentiment score (-1 to +1)."""
    color = (
        COLORS["bullish"] if score > 0.15
        else COLORS["bearish"] if score < -0.15
        else COLORS["neutral"]
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number=dict(valueformat=".3f", font=dict(color=COLORS["text"])),
        delta=dict(reference=0, valueformat=".3f"),
        gauge=dict(
            axis=dict(range=[-1, 1], tickwidth=1, tickcolor=COLORS["border"],
                      tickfont=dict(color=COLORS["muted"])),
            bar=dict(color=color, thickness=0.3),
            bgcolor=COLORS["surface"],
            borderwidth=0,
            steps=[
                dict(range=[-1, -0.15], color="rgba(244,63,94,0.15)"),
                dict(range=[-0.15, 0.15], color="rgba(148,163,184,0.1)"),
                dict(range=[0.15, 1], color="rgba(16,185,129,0.15)"),
            ],
            threshold=dict(line=dict(color=COLORS["text"], width=2), thickness=0.75, value=score),
        ),
        title=dict(text=f"{symbol} Sentiment", font=dict(size=13, color=COLORS["muted"])),
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        height=200,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    return fig


def prediction_confidence_chart(predictions: list[dict]) -> go.Figure:
    """Horizontal bar chart showing prediction confidence for each symbol."""
    symbols = [p["symbol"] for p in predictions]
    confidences = [p["confidence"] * 100 for p in predictions]
    directions = [p["direction"] for p in predictions]
    colors = [
        COLORS["bullish"] if d == "bullish" else COLORS["bearish"]
        for d in directions
    ]

    fig = go.Figure(go.Bar(
        x=confidences,
        y=symbols,
        orientation="h",
        marker_color=colors,
        text=[f"{c:.0f}% {d.upper()}" for c, d in zip(confidences, directions)],
        textposition="inside",
        insidetextanchor="middle",
    ))

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text="AI Prediction Confidence", font=dict(size=14)),
        xaxis=dict(range=[0, 100], title="Confidence %", gridcolor=COLORS["border"]),
        height=200,
    )
    return fig
