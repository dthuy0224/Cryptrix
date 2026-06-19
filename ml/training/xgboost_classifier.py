import os
import pandas as pd
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, log_loss
from app.utils.logger import logger

def generate_mock_features(samples: int = 1000) -> pd.DataFrame:
    """Generates synthetic price data and calculated indicators for model training."""
    np.random.seed(42)
    
    # Generate prices
    base_price = 60000.0
    prices = [base_price]
    for _ in range(samples - 1):
        prices.append(prices[-1] * (1 + np.random.normal(0.0002, 0.015)))
        
    df = pd.DataFrame({"price": prices})
    
    # Compute mockup indicators
    df["sma_14"] = df["price"].rolling(window=14).mean().fillna(base_price)
    df["rsi"] = np.random.uniform(20, 80, samples) # Mock RSI
    
    # Compute target: 1 (bullish) if next price is higher than current price, else 0
    df["target"] = (df["price"].shift(-1) > df["price"]).astype(int)
    
    # Return features (drop target for features dataframe)
    return df.dropna()

def train_market_classifier():
    """
    Trains an XGBoost classification model to predict market directions.
    Params and metrics are logged automatically to an MLflow Tracking Server.
    """
    # Configure MLflow
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "cryptrix-market-forecasting")
    mlflow.set_experiment(experiment_name)
    
    # Ingest data
    logger.info("Generating feature datasets for XGBoost model training...")
    data = generate_mock_features()
    
    X = data[["price", "sma_14", "rsi"]]
    y = data["target"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Model parameters
    params = {
        "max_depth": 5,
        "learning_rate": 0.05,
        "n_estimators": 100,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": 42
    }
    
    logger.info("Initializing MLflow tracking run...")
    with mlflow.start_run() as run:
        # Log training hyperparameters
        mlflow.log_params(params)
        
        # Initialize and train classifier
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        # Calculate test predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Compute performance metrics
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        loss = log_loss(y_test, y_prob)
        
        logger.info(f"Model Training complete. Metrics - Accuracy: {acc:.4f}, F1: {f1:.4f}")
        
        # Log metrics to MLflow
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("log_loss", loss)
        
        # Save model run details as artifact
        mlflow.xgboost.log_model(
            xgb_model=model,
            artifact_path="model",
            registered_model_name="Cryptrix-BTC-XGB"
        )
        
        logger.info(f"MLflow Run ID completed: {run.info.run_id}")
        return run.info.run_id

if __name__ == "__main__":
    train_market_classifier()
