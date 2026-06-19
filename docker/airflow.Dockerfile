# ==========================================
# Custom Apache Airflow Runner Dockerfile
# ==========================================
# Adds Python library layers to standard Airflow images.

FROM apache/airflow:2.9.1-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    pandas==2.2.1 \
    numpy==1.26.4 \
    requests==2.31.0 \
    google-cloud-storage==2.15.0 \
    google-cloud-bigquery==3.18.0 \
    great-expectations==0.18.12
