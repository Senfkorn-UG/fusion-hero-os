output "instance_name" {
  value = google_compute_instance.tailscale_router.name
}

output "instance_zone" {
  value = google_compute_instance.tailscale_router.zone
}

output "internal_ip" {
  value = google_compute_instance.tailscale_router.network_interface[0].network_ip
}

output "external_ip" {
  value = google_compute_instance.tailscale_router.network_interface[0].access_config[0].nat_ip
}

output "subnet_cidr" {
  value = var.subnet_cidr
}

output "tailscale_next_steps" {
  value = <<-EOT
    1. Approve subnet route ${var.subnet_cidr} in Tailscale Admin -> Machines -> Subnet routes
    2. If exit node enabled, approve exit node for this machine
    3. SSH: gcloud compute ssh ${google_compute_instance.tailscale_router.name} --zone=${var.zone}
  EOT
}
