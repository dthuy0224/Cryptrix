variable "project_id" {
  description = "The Google Cloud Platform Project ID"
  type        = string
  default     = "cryptrix-production-42"
}

variable "region" {
  description = "Primary deployment region for cloud resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Availability zone for region"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Deployment environment namespace"
  type        = string
  default     = "production"
}
