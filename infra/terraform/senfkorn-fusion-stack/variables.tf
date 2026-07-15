variable "project_id" {
  type        = string
  description = "Google Cloud project ID"
  # Set explicitly: terraform apply -var="project_id=my-gcp-project"
  default     = ""
}

variable "region" {
  type        = string
  description = "GCP region for GKE and storage"
  default     = "europe-west3"
}

variable "cluster_name" {
  type        = string
  description = "Existing GKE Autopilot cluster name"
  default     = "senfkorn-gke-cluster"
}

variable "bucket_name" {
  type        = string
  description = "GCS bucket for Fusion training data and checkpoints"
  default     = ""
}

variable "training_namespace" {
  type        = string
  default     = "fusion-training"
}