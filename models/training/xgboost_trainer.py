"""
XGBoost Market Direction Classifier
=====================================
Trains a binary classification model to predict BTC/ETH/SOL price direction.

Pipeline:
  1. Load feature-engineered data (from data/features/)
  2. Train/validation/test split (time-series aware — no shuffle)
  3. Train XGBoost classifier with hyperparameter logging
  4. Evaluate: accuracy, F1, log-loss, ROC-AUC
  5. Log everything to MLflow
  6. Register best model in MLflow Model Registry

Usage:
  python models/training/xgboost_trainer.py --symbol BTC
"""
import argparse
import os
import numpy as np
import pandas as pd
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.metrics import (
    accuracy_score, f1_score, log_loss, roc_auc_score, classification_report
)
from pathlib import Path

from utils import logger
from pipelines.loaders.local_loader import loader

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "cryptrix-market-forecasting")

FEATURE_COLS = [
    "close", "volume",
    "sma_7", "sma_14", "sma_30",
    "ema_9", "ema_21",
    "rsi",
    "macd_line", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width",
    "atr", "obv",
]
TARGET_COL = "target"

XGBOOST_PARAMS = {
    "max_depth": 5,
    "learning_rate": 0.05,
    "n_estimators": 300,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "random_state": 42,
    "n_jobs": -1,
}


# ---------------------------------------------------------------------------
# Data Prep
# ---------------------------------------------------------------------------

def load_training_data(symbol: str) -> tuple[pd.DataFrame, pd.Series]:
    """Load features and validate training data for a symbol."""
    df = loader.load_features(symbol)
    if df.empty:
        raise FileNotFoundError(
            f"No features found for {symbol}. Run ETL pipeline first:\n"
            "  python pipelines/ingestion/binance_client.py\n"
            "  python pipelines/transformation/features.py"
        )

    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")

    # Drop rows where target is NaN (last row after lookahead shift)
    df = df.dropna(subset=[TARGET_COL] + FEATURE_COLS)

    X = df[FEATURE_COLS]
    y = df[TARGET_COL].astype(int)

    logger.info(f"[Trainer] Loaded {len(df)} samples for {symbol}")
    logger.info(f"[Trainer] Class distribution: {y.value_counts().to_dict()}")
    return X, y


def time_series_split(X: pd.DataFrame, y: pd.Series, test_ratio: float = 0.15, val_ratio: float = 0.10):
    """
    Time-series aware split — NO shuffle (preserves temporal order).
    Split: train | val | test (chronological)
    """
    n = len(X)
    test_start = int(n * (1 - test_ratio))
    val_start = int(n * (1 - test_ratio - val_ratio))

    X_train, y_train = X.iloc[:val_start], y.iloc[:val_start]
    X_val, y_val = X.iloc[val_start:test_start], y.iloc[val_start:test_start]
    X_test, y_test = X.iloc[test_start:], y.iloc[test_start:]

    logger.info(
        f"[Trainer] Split → Train:{len(X_train)} | Val:{len(X_val)} | Test:{len(X_test)}"
    )
    return X_train, y_train, X_val, y_val, X_test, y_test


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_classifier(symbol: str, register: bool = True) -> str:
    """
    Full training pipeline: load → split → train → evaluate → log to MLflow.
    Returns the MLflow run_id.
    """
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    X, y = load_training_data(symbol)
    X_train, y_train, X_val, y_val, X_test, y_test = time_series_split(X, y)

    with mlflow.start_run(run_name=f"{symbol}-XGBoost-{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}") as run:
        # Log params
        mlflow.log_param("symbol", symbol)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("feature_count", len(FEATURE_COLS))
        mlflow.log_params(XGBOOST_PARAMS)

        # Train
        logger.info(f"[Trainer] Training XGBoost for {symbol}...")
        model = xgb.XGBClassifier(**XGBOOST_PARAMS)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # Evaluate on test set
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        ll = log_loss(y_test, y_prob)
        auc = roc_auc_score(y_test, y_prob)

        logger.info(
            f"[Trainer] {symbol} Results → "
            f"Acc: {acc:.4f} | F1: {f1:.4f} | AUC: {auc:.4f} | LogLoss: {ll:.4f}"
        )
        logger.info(f"\n{classification_report(y_test, y_pred, target_names=['Bearish', 'Bullish'])}")

        # Log metrics
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("log_loss", ll)
        mlflow.log_metric("roc_auc", auc)

        # Log model
        registered_name = f"Cryptrix-{symbol}-XGBoost" if register else None
        mlflow.xgboost.log_model(
            xgb_model=model,
            artifact_path="model",
            registered_model_name=registered_name,
        )

        # Save locally as backup
        local_path = Path(f"models/saved_models/{symbol.lower()}_xgb.json")
        model.save_model(local_path)
        logger.info(f"[Trainer] Model saved locally → {local_path}")

        run_id = run.info.run_id
        logger.info(f"[Trainer] MLflow run completed: {run_id}")
        return run_id


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost market classifier")
    parser.add_argument("--symbol", default="BTC", help="Symbol to train on (BTC/ETH/SOL)")
    parser.add_argument("--no-register", action="store_true", help="Skip MLflow model registration")
    args = parser.parse_args()

    run_id = train_classifier(args.symbol.upper(), register=not args.no_register)
    print(f"\n✅ Training complete. MLflow Run ID: {run_id}")
