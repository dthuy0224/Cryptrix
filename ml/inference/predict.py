import os
import requests
import numpy as np
import xgboost as xgb
import mlflow.xgboost
from app.utils.logger import logger

class InferenceEngine:
    """
    ML serving layer. Handles model loading from MLflow registry and performs
    high-concurrency predictions pushed to FastAPI servers.
    """
    def __init__(self, model_uri: str = "models:/Cryptrix-BTC-XGB/Production"):
        self.model_uri = model_uri
        self.model = None

    def load_model(self):
        """Loads model binary using MLflow APIs."""
        try:
            logger.info(f"Loading registered model from URI: {self.model_uri}")
            # Emulated load: fallback to local model if MLflow not running in dev sandbox
            self.model = mlflow.xgboost.load_model(self.model_uri)
        except Exception as e:
            logger.warning(f"Could not load from MLflow Registry: {e}. Emulating placeholder model.")
            # Build quick fallback model for local dev/demo verification
            self.model = xgb.XGBClassifier()
            # Simple mock fit
            self.model.fit(np.array([[50000.0, 50000.0, 50.0]]), np.array([1]))

    def predict_and_publish(self, price: float, sma: float, rsi: float):
        """
        Executes prediction checks and broadcasts them to the active serving endpoints.
        """
        if self.model is None:
            self.load_model()
            
        features = np.array([[price, sma, rsi]])
        
        # Predict trend classification
        pred_class = int(self.model.predict(features)[0])
        pred_prob = float(self.model.predict_proba(features)[0][pred_class])
        
        direction = "bullish" if pred_class == 1 else "bearish"
        predicted_price = price * (1 + (0.015 * (1 if pred_class == 1 else -1)))
        
        payload = {
            "symbol": "BTC",
            "current_price": price,
            "predicted_price": float(round(predicted_price, 2)),
            "direction": direction,
            "confidence": float(round(pred_prob, 2)),
            "model_name": "XGBoost v2.1-Classifier",
            "horizon": "24h"
        }
        
        backend_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1") + "/ml/predict"
        
        try:
            logger.info(f"Publishing prediction to API endpoint: {backend_url}")
            response = requests.post(backend_url, json=payload, timeout=5)
            logger.info(f"FastAPI Broadcast Completed. Response Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to post prediction to API gateway: {e}")

if __name__ == "__main__":
    # Test local visual execution
    engine = InferenceEngine()
    engine.predict_and_publish(68425.50, 68000.0, 65.5)
