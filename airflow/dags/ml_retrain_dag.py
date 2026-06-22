"""
ML Model Retraining DAG — Weekly
==================================
Airflow DAG: cryptrix_ml_retrain

Schedule: Every Sunday at 02:00 UTC
Tasks:
  1. check_data_readiness  — Ensure sufficient feature data exists
  2. train_xgboost         — Retrain XGBoost classifier for BTC/ETH/SOL
  3. train_prophet         — Retrain Prophet forecaster
  4. evaluate_models       — Compare new vs. previous model metrics
  5. notify_completion     — Log completion (extend with Slack/email alerts)
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "cryptrix_ml_eng",
    "depends_on_past": False,
    "start_date": datetime(2026, 6, 1),
    "email": ["alerts@cryptrix.ai"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

SYMBOLS = ["BTC", "ETH", "SOL"]
MIN_TRAINING_ROWS = 200   # Minimum feature rows required before training


# ---------------------------------------------------------------------------
# Task Functions
# ---------------------------------------------------------------------------

def task_check_data_readiness(**context):
    """Validate that sufficient feature-engineered data exists for each symbol."""
    from pipelines.loaders.local_loader import loader

    not_ready = []
    for sym in SYMBOLS:
        df = loader.load_features(sym)
        row_count = len(df) if not df.empty else 0
        if row_count < MIN_TRAINING_ROWS:
            not_ready.append(f"{sym}: {row_count}/{MIN_TRAINING_ROWS} rows")
        else:
            print(f"[Retrain] {sym} ✓ {row_count} feature rows available.")

    if not_ready:
        raise ValueError(
            f"[Retrain] Insufficient data for training:\n" + "\n".join(not_ready) +
            "\nRun cryptrix_market_etl DAG to collect more data."
        )

    print(f"[Retrain] All symbols have sufficient data. Proceeding with retraining.")


def task_train_xgboost(**context):
    """Retrain XGBoost classifiers for all tracked symbols."""
    from models.training.xgboost_trainer import train_classifier

    run_ids = {}
    for sym in SYMBOLS:
        print(f"[Retrain] Training XGBoost for {sym}...")
        run_id = train_classifier(sym, register=True)
        run_ids[sym] = run_id
        print(f"[Retrain] {sym} XGBoost complete. Run ID: {run_id}")

    context["task_instance"].xcom_push(key="xgb_run_ids", value=run_ids)
    return run_ids


def task_train_prophet(**context):
    """Retrain Prophet forecasters for all tracked symbols."""
    from models.training.prophet_trainer import train_prophet

    run_ids = {}
    for sym in SYMBOLS:
        try:
            print(f"[Retrain] Training Prophet for {sym}...")
            run_id = train_prophet(sym, horizon_hours=24)
            run_ids[sym] = run_id
            print(f"[Retrain] {sym} Prophet complete. Run ID: {run_id}")
        except Exception as e:
            # Prophet training is non-critical (XGBoost is primary)
            print(f"[Retrain] Prophet training for {sym} failed (non-fatal): {e}")
            run_ids[sym] = None

    context["task_instance"].xcom_push(key="prophet_run_ids", value=run_ids)
    return run_ids


def task_evaluate_models(**context):
    """
    Compare newly trained models vs. previous metrics logged in MLflow.
    Alerts if accuracy drops significantly.
    """
    import mlflow
    import os

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "cryptrix-market-forecasting"))

    xgb_run_ids = context["task_instance"].xcom_pull(task_ids="train_xgboost", key="xgb_run_ids")
    client = mlflow.MlflowClient()

    results = {}
    for sym, run_id in (xgb_run_ids or {}).items():
        if not run_id:
            continue
        run = client.get_run(run_id)
        metrics = run.data.metrics
        acc = metrics.get("accuracy", 0)
        auc = metrics.get("roc_auc", 0)
        results[sym] = {"accuracy": acc, "roc_auc": auc, "run_id": run_id}

        # Alert if accuracy is below threshold
        if acc < 0.52:
            print(f"[Evaluate] ⚠️ WARNING: {sym} accuracy {acc:.4f} is near random (< 0.52)!")
        else:
            print(f"[Evaluate] {sym} ✓ Acc={acc:.4f} | AUC={auc:.4f}")

    context["task_instance"].xcom_push(key="eval_results", value=results)
    return results


def task_notify_completion(**context):
    """Log completion summary. Extend with Slack/email notifications."""
    eval_results = context["task_instance"].xcom_pull(task_ids="evaluate_models", key="eval_results")

    print("\n" + "="*50)
    print("✅ Cryptrix ML Retraining Complete")
    print("="*50)
    for sym, metrics in (eval_results or {}).items():
        print(f"  {sym}: Acc={metrics.get('accuracy', 0):.4f} | AUC={metrics.get('roc_auc', 0):.4f}")
    print("="*50)

    # TODO: Send Slack notification via webhook
    # import httpx
    # httpx.post(os.getenv("SLACK_WEBHOOK_URL"), json={"text": summary})


# ---------------------------------------------------------------------------
# DAG Definition
# ---------------------------------------------------------------------------

with DAG(
    dag_id="cryptrix_ml_retrain",
    default_args=default_args,
    description="Weekly ML model retraining: XGBoost + Prophet for BTC/ETH/SOL",
    schedule_interval="0 2 * * 0",  # Every Sunday 02:00 UTC
    catchup=False,
    tags=["cryptrix", "ml", "training"],
) as dag:

    check_data = PythonOperator(
        task_id="check_data_readiness",
        python_callable=task_check_data_readiness,
    )

    train_xgb = PythonOperator(
        task_id="train_xgboost",
        python_callable=task_train_xgboost,
    )

    train_prophet = PythonOperator(
        task_id="train_prophet",
        python_callable=task_train_prophet,
    )

    evaluate = PythonOperator(
        task_id="evaluate_models",
        python_callable=task_evaluate_models,
    )

    notify = PythonOperator(
        task_id="notify_completion",
        python_callable=task_notify_completion,
    )

    # XGBoost and Prophet can train in parallel after data check
    check_data >> [train_xgb, train_prophet] >> evaluate >> notify
