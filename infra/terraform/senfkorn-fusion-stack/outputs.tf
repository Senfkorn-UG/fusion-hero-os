output "bucket_name" {
  value = google_storage_bucket.fusion_ai_data.name
}

output "bucket_url" {
  value = "gs://${google_storage_bucket.fusion_ai_data.name}"
}

output "training_service_account" {
  value = google_service_account.fusion_training.email
}

output "workload_identity_annotation" {
  value = "iam.gke.io/gcp-service-account=${google_service_account.fusion_training.email}"
}