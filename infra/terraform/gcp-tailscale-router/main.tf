resource "google_compute_network" "vpc" {
  name                    = "senfkorn-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "senfkorn-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "senfkorn-allow-ssh"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["tailscale-router"]
}

resource "google_compute_firewall" "allow_tailscale_udp" {
  name    = "senfkorn-allow-tailscale-udp"
  network = google_compute_network.vpc.name

  allow {
    protocol = "udp"
    ports    = ["41641"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["tailscale-router"]
}

resource "google_service_account" "tailscale_sa" {
  account_id   = "tailscale-router-sa"
  display_name = "Service Account for Tailscale subnet router"
}

resource "google_compute_instance" "tailscale_router" {
  name         = "tailscale-subnet-router"
  machine_type = "e2-micro"
  zone         = var.zone

  can_ip_forward = true
  tags           = ["tailscale-router"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id

    access_config {}
  }

  service_account {
    email  = google_service_account.tailscale_sa.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = templatefile("${path.module}/startup.sh.tftpl", {
    tailscale_auth_key   = var.tailscale_auth_key
    subnet_cidr          = var.subnet_cidr
    advertise_exit_node  = var.advertise_exit_node
    instance_name        = "tailscale-subnet-router"
  })

  lifecycle {
    create_before_destroy = true
  }
}
