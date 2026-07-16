variable "project_id" {
  type        = string
  description = "Google Cloud project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "europe-west3"
}

variable "zone" {
  type        = string
  description = "GCP zone"
  default     = "europe-west3-a"
}

variable "subnet_cidr" {
  type        = string
  description = "Private subnet advertised into the tailnet"
  default     = "10.0.1.0/24"
}

variable "tailscale_auth_key" {
  type        = string
  description = "Reusable or ephemeral Tailscale auth key. Leave empty for manual registration."
  default     = ""
  sensitive   = true
}

variable "advertise_exit_node" {
  type        = bool
  description = "Advertise this VM as a tailnet exit node (requires admin approval)"
  default     = true
}
