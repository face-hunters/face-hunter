terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "3.5.0"
    }
  }
}

provider "google" {
  credentials = file("face-hunter.json")

  project = "face-hunter-319522"
  region  = "europe-west2"
  zone    = "europe-west2-c"
}

resource "google_compute_disk" "default" {
  name  = "test-disk"
  type  = "pd-ssd"
  zone  = "europe-west2-c"
  image = "debian-9-stretch-v20200805"
  labels = {
    environment = "dev"
  }
  physical_block_size_bytes = 4096
}

resource "google_compute_instance" "default" {
  name         = "attached-disk-instance"
  machine_type = "e2-medium"
  zone         = "europe-west2-c"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  network_interface {
    network = "default"
  }

  lifecycle {
    ignore_changes = [attached_disk]
  }
}

resource "google_compute_attached_disk" "default" {
  disk     = google_compute_disk.default.id
  instance = google_compute_instance.default.id
}