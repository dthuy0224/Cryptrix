output "raw_bucket_url" {
  description = "GCS raw bucket entrypoint URI"
  value       = google_storage_bucket.raw_data_lake.url
}

output "silver_bucket_url" {
  description = "GCS silver bucket entrypoint URI"
  value       = google_storage_bucket.silver_transformed.url
}

output "bigquery_analytics_dataset_id" {
  description = "Google BigQuery Analytics dataset reference ID"
  value       = google_bigquery_dataset.analytics_dataset.dataset_id
}

output "backend_api_url" {
  description = "google Cloud Run API backend serving endpoint URL"
  value       = google_cloud_run_service.backend_api.status[0].url
}
