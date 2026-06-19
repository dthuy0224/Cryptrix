from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import random

# Default Airflow settings
default_args = {
    'owner': 'cryptrix_data_eng',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 20),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

def analyze_community_sentiment(**context):
    """
    Airflow task: Pulls mock post streams, runs sentiment extraction pipelines,
    and returns a cumulative polarity score from -1.0 to 1.0.
    """
    symbols = ["BTC", "ETH", "SOL"]
    
    for symbol in symbols:
        # Simulate sentiment score calculation
        score = random.uniform(-0.2, 0.8) # Bullish leaning random sentiment score
        label = "positive" if score > 0.15 else ("negative" if score < -0.15 else "neutral")
        mentions = random.randint(100, 5000)
        
        # Local mock backend push (represents real-time web sync)
        print(f"Scored {symbol} sentiment index: {score:.2f} ({label.upper()}). Mentions: {mentions}")
        
        # In a real workflow, we would push this payload to:
        # http://localhost:8000/api/v1/market/sentiment
        
with DAG(
    'cryptrix_social_sentiment_analysis',
    default_args=default_args,
    description='Aggregates social mentions and scores market sentiment metrics',
    schedule_interval='*/15 * * * *', # Executes every 15 minutes
    catchup=False,
) as dag:

    task_sentiment = PythonOperator(
        task_id='calculate_sentiment_index',
        python_callable=analyze_community_sentiment,
    )
