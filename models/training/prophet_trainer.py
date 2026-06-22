"""
Prophet Time-Series Forecaster
================================
Trains a Facebook Prophet model to predict hourly BTC/ETH/SOL prices.
Prophet is specifically designed for time-series with seasonality.

Usage:
  python models/training/prophet_trainer.py --symbol BTC --horizon 24
"""
import argparse
import os
import pandas as pd
import mlflow
from pathlib import Path

from utils import logger
from pipelines.loaders.local_loader import loader

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "cryptrix-market-forecasting")


def prepare_prophet_data(symbol: str) -> pd.DataFrame:
    """
    Load OHLCV and format for Prophet: columns must be 'ds' (datetime) and 'y' (value).
    """
    df = loader.load_ohlcv(symbol, interval="1h")
    if df.empty:
        raise FileNotFoundError(
            f"No OHLCV data for {symbol}. Run ETL pipeline first."
        )

    prophet_df = pd.DataFrame({
        "ds": pd.to_datetime(df["timestamp"]).dt.tz_localize(None),  # Prophet needs tz-naive
        "y": df["close"].astype(float),
    }).dropna().sort_values("ds").reset_index(drop=True)

    logger.info(f"[Prophet] Prepared {len(prophet_df)} rows for {symbol}")
    return prophet_df


def train_prophet(symbol: str, horizon_hours: int = 24) -> str:
    """
    Train a Prophet model and log to MLflow.
    Returns MLflow run_id.
    """
    try:
        from prophet import Prophet
        from prophet.diagnostics import cross_validation, performance_metrics
    except ImportError:
        raise ImportError("Install prophet: pip install prophet")

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    df = prepare_prophet_data(symbol)
    train_df = df.iloc[:-horizon_hours]   # Hold out last N hours for eval
    test_df = df.iloc[-horizon_hours:]

    with mlflow.start_run(run_name=f"{symbol}-Prophet-{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}") as run:
        mlflow.log_param("symbol", symbol)
        mlflow.log_param("train_rows", len(train_df))
        mlflow.log_param("horizon_hours", horizon_hours)
        mlflow.log_param("model_type", "Prophet")

        logger.info(f"[Prophet] Training on {len(train_df)} rows for {symbol}...")

        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,    # Flexibility of trend changepoints
            seasonality_prior_scale=10.0,
            interval_width=0.8,              # 80% uncertainty interval
        )
        model.add_seasonality(name="hourly", period=1/24, fourier_order=5)
        model.fit(train_df)

        # Forecast
        future = model.make_future_dataframe(periods=horizon_hours, freq="h")
        forecast = model.predict(future)

        # Evaluate against test set
        forecast_test = forecast.tail(horizon_hours)
        actual = test_df["y"].values
        predicted = forecast_test["yhat"].values

        mae = float(abs(actual - predicted).mean())
        mape = float((abs((actual - predicted) / actual)).mean() * 100)
        rmse = float(((actual - predicted) ** 2).mean() ** 0.5)

        logger.info(f"[Prophet] {symbol} Evaluation → MAE: {mae:.2f} | MAPE: {mape:.2f}% | RMSE: {rmse:.2f}")

        mlflow.log_metric("mae", mae)
        mlflow.log_metric("mape_pct", mape)
        mlflow.log_metric("rmse", rmse)

        # Save forecast as artifact
        forecast_path = Path(f"models/saved_models/{symbol.lower()}_prophet_forecast.csv")
        forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(forecast_path, index=False)
        mlflow.log_artifact(str(forecast_path))

        # Save model (pickle via mlflow)
        mlflow.prophet.log_model(
            pr_model=model,
            artifact_path="prophet_model",
            registered_model_name=f"Cryptrix-{symbol}-Prophet",
        )

        run_id = run.info.run_id
        logger.info(f"[Prophet] MLflow run completed: {run_id}")
        return run_id


def get_prophet_forecast(symbol: str) -> pd.DataFrame | None:
    """Load the latest saved Prophet forecast for a symbol."""
    path = Path(f"models/saved_models/{symbol.lower()}_prophet_forecast.csv")
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["ds"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Prophet time-series forecaster")
    parser.add_argument("--symbol", default="BTC", help="Symbol (BTC/ETH/SOL)")
    parser.add_argument("--horizon", type=int, default=24, help="Forecast horizon in hours")
    args = parser.parse_args()

    run_id = train_prophet(args.symbol.upper(), horizon_hours=args.horizon)
    print(f"\n✅ Prophet training complete. MLflow Run ID: {run_id}")
