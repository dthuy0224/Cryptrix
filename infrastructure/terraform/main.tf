# ==============================================================================
# Cryptrix Google Cloud Platform Landing Zone Infrastructure
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.15.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ------------------------------------------------------------------------------
# Google Cloud Storage (GCS) Buckets - Data Lake House
# ------------------------------------------------------------------------------

# Raw Storage (JSON Ingests from APIs)
resource "google_storage_bucket" "raw_data_lake" {
  name          = "cryptrix-raw-data-lake-${var.environment}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90 # Transition raw files to cold line storage after 90 days
    }
    action {
      type = "Delete"
    }
  }
}

# Transformed Storage (Cleaned Parquet Features)
resource "google_storage_bucket" "silver_transformed" {
  name          = "cryptrix-silver-transformed-${var.environment}"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true
}

# ------------------------------------------------------------------------------
# Google BigQuery - golden warehouse schemas
# ------------------------------------------------------------------------------

resource "google_bigquery_dataset" "analytics_dataset" {
  dataset_id                  = "cryptrix_analytics_${var.environment}"
  friendly_name               = "Cryptrix Analytics Warehouse"
  description                 = "Consolidated metrics, indicator features, and predictions database."
  location                    = var.region
  default_table_expiration_ms = 31536000000 # 365 Days
}

# BigQuery Table: Realtime Tickers
resource "google_bigquery_table" "market_prices" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "market_prices"
  
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = <<EOF
[
  {
    "name": "symbol",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Cryptocurrency pair ticker base"
  },
  {
    "name": "price",
    "type": "FLOAT",
    "mode": "REQUIRED",
    "description": "Ticker closing value in USD"
  },
  {
    "name": "change_24h",
    "type": "FLOAT",
    "mode": "NULLABLE"
  },
  {
    "name": "volume_24h",
    "type": "FLOAT",
    "mode": "NULLABLE"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  }
]
EOF
}

# BigQuery Table: AI Predictions
resource "google_bigquery_table" "prediction_results" {
  dataset_id = google_bigquery_dataset.analytics_dataset.dataset_id
  table_id   = "prediction_results"

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = <<EOF
[
  {
    "name": "symbol",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "current_price",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "predicted_price",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "direction",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "confidence",
    "type": "FLOAT",
    "mode": "REQUIRED"
  },
  {
    "name": "model_name",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  }
]
EOF
}

# ------------------------------------------------------------------------------
# Google Cloud Run - Serving Layer Deployments
# ------------------------------------------------------------------------------

# FastAPI Backend Service
resource "google_cloud_run_service" "backend_api" {
  name     = "cryptrix-backend-api"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/cryptrix-backend:latest"
        ports {
          container_port = 8000
        }
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}
