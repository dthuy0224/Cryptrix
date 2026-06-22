"""
Unified Prediction Engine
==========================
Loads trained models (XGBoost from MLflow or local fallback)
and generates market direction predictions.

Usage:
  from models.inference.predict import PredictionEngine
  engine = PredictionEngine()
  result = engine.predict("BTC")
"""
import os
import numpy as np
import xgboost as xgb
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from utils import logger
from pipelines.loaders.local_loader import loader

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

FEATURE_COLS = [
    "close", "volume",
    "sma_7", "sma_14", "sma_30",
    "ema_9", "ema_21",
    "rsi",
    "macd_line", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width",
    "atr", "obv",
]


class PredictionEngine:
    """
    Loads models from MLflow registry (or local fallback) and runs inference.
    """

    def __init__(self):
        self._models: dict[str, xgb.XGBClassifier] = {}

    def _load_model(self, symbol: str) -> xgb.XGBClassifier:
        """Load model: MLflow registry → local file → untrained fallback."""
        if symbol in self._models:
            return self._models[symbol]

        # 1. Try loading from MLflow
        try:
            import mlflow.xgboost
            mlflow.set_tracking_uri(MLFLOW_URI)
            model_uri = f"models:/Cryptrix-{symbol}-XGBoost/Production"
            logger.info(f"[Inference] Loading model from MLflow: {model_uri}")
            model = mlflow.xgboost.load_model(model_uri)
            self._models[symbol] = model
            return model
        except Exception as e:
            logger.warning(f"[Inference] MLflow unavailable: {e}")

        # 2. Try local saved model
        local_path = Path(f"models/saved_models/{symbol.lower()}_xgb.json")
        if local_path.exists():
            logger.info(f"[Inference] Loading local model: {local_path}")
            model = xgb.XGBClassifier()
            model.load_model(local_path)
            self._models[symbol] = model
            return model

        # 3. Untrained fallback (demo only — logs warning)
        logger.warning(
            f"[Inference] No trained model found for {symbol}. "
            "Using demo model. Run training first: python models/training/xgboost_trainer.py"
        )
        model = xgb.XGBClassifier(n_estimators=10, max_depth=3, random_state=42)
        # Minimal fit to make predict_proba available
        dummy_X = np.array([[60000, 1000, 59000, 58000, 57000, 59500, 59800, 55, 100, 80, 20, 62000, 58000, 3.0, 500, 1e6]])
        dummy_y = np.array([1])
        model.fit(dummy_X, dummy_y)
        self._models[symbol] = model
        return model

    def predict(self, symbol: str) -> dict[str, Any]:
        """
        Generate a prediction for a symbol using the latest available features.

        Returns:
            {
              symbol, current_price, predicted_price, direction,
              confidence, model_name, horizon, timestamp
            }
        """
        df = loader.load_features(symbol)

        if df.empty or len(df) < 5:
            logger.warning(f"[Inference] Insufficient data for {symbol}. Running ETL pipeline first.")
            return self._fallback_prediction(symbol)

        # Use the latest row for inference
        latest = df.iloc[-1]

        # Build feature vector
        missing = [c for c in FEATURE_COLS if c not in df.columns]
        if missing:
            logger.error(f"[Inference] Missing features: {missing}")
            return self._fallback_prediction(symbol)

        X = latest[FEATURE_COLS].values.reshape(1, -1)

        model = self._load_model(symbol)
        pred_class = int(model.predict(X)[0])
        pred_proba = model.predict_proba(X)[0]
        confidence = float(pred_proba[pred_class])

        direction = "bullish" if pred_class == 1 else "bearish"
        current_price = float(latest["close"])

        # Simple price projection (±1.5% over 24h)
        price_change_pct = 0.015 if pred_class == 1 else -0.015
        predicted_price = round(current_price * (1 + price_change_pct), 2)

        result = {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "predicted_price": predicted_price,
            "direction": direction,
            "confidence": round(confidence, 4),
            "model_name": "XGBoost-v2-Classifier",
            "horizon": "24h",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features_used": len(FEATURE_COLS),
        }

        logger.info(
            f"[Inference] {symbol}: {direction.upper()} | "
            f"${current_price:,.2f} → ${predicted_price:,.2f} | "
            f"Confidence: {confidence:.1%}"
        )
        return result

    def predict_batch(self, symbols: list[str]) -> list[dict[str, Any]]:
        """Generate predictions for multiple symbols."""
        return [self.predict(sym) for sym in symbols]

    def _fallback_prediction(self, symbol: str) -> dict[str, Any]:
        """Return a placeholder prediction when data/model is unavailable."""
        return {
            "symbol": symbol.upper(),
            "current_price": 0.0,
            "predicted_price": 0.0,
            "direction": "neutral",
            "confidence": 0.0,
            "model_name": "fallback",
            "horizon": "24h",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "Model or data not available. Run ETL and training pipelines.",
        }


# Singleton for import
engine = PredictionEngine()


if __name__ == "__main__":
    results = engine.predict_batch(["BTC", "ETH", "SOL"])
    for r in results:
        print(
            f"{r['symbol']}: {r['direction'].upper()} | "
            f"${r['current_price']:,.2f} → ${r['predicted_price']:,.2f} | "
            f"Conf: {r['confidence']:.1%}"
        )
