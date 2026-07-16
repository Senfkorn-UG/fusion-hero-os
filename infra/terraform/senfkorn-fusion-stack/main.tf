# Senfkorn UG — Fusion AI Tier-2 training stack (GCS + Workload Identity for GKE)
# GKE cluster senfkorn-gke-cluster is assumed to already exist (Autopilot).

resource "google_storage_bucket" "fusion_ai_data" {
  name                        = var.bucket_name
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = {
    org     = "senfkorn-ug"
    purpose = "fusion-ai-training"
    tier    = "tier2-a100"
  }
}

resource "google_service_account" "fusion_training" {
  account_id   = "fusion-training-sa"
  display_name = "Fusion AI training workload (GKE)"
}

resource "google_storage_bucket_iam_member" "fusion_training_object_admin" {
  bucket = google_storage_bucket.fusion_ai_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.fusion_training.email}"
}

resource "google_project_iam_member" "fusion_training_gke_viewer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.fusion_training.email}"
}

resource "google_service_account_iam_member" "fusion_training_wi" {
  service_account_id = google_service_account.fusion_training.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.training_namespace}/fusion-training-ksa]"
}

# Coordination CronJob (fusion-coordination NS) reuses same GSA + objectAdmin
resource "google_service_account_iam_member" "fusion_coordination_wi" {
  service_account_id = google_service_account.fusion_training.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[fusion-coordination/fusion-coordination-ksa]"
}