import pandas as pd
import numpy as np

def calculate_simple_moving_average(df: pd.DataFrame, window: int = 14, column: str = "price") -> pd.Series:
    """Calculates SMA for a given price series window."""
    return df[column].rolling(window=window).mean()

def calculate_relative_strength_index(df: pd.DataFrame, period: int = 14, column: str = "price") -> pd.Series:
    """
    Computes Relative Strength Index (RSI), a popular technical indicator
    used to measure speed and change of price movements.
    """
    delta = df[column].diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()
    
    # Calculate exponential moving averages
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50) # Fallback to neutral 50 for initial window gap

def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, column: str = "price") -> pd.DataFrame:
    """
    Computes MACD line, Signal line, and MACD Histogram.
    """
    fast_ema = df[column].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df[column].ewm(span=slow_period, adjust=False).mean()
    
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    return pd.DataFrame({
        "macd_line": macd_line,
        "macd_signal": signal_line,
        "macd_histogram": macd_hist
    })
