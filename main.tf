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

  project = var.project_name
  region  = var.region
  zone    = "${var.region}-c"
}

resource "google_compute_firewall" "firewall" {
  name    = "gritfy-firewall-externalssh"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["${chomp(data.http.my_ip.body)}/32"]
  target_tags   = ["externalssh"]
}

resource "google_compute_firewall" "webserverrule" {
  name    = "gritfy-webserver"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["80","443"]
  }
  source_ranges = ["${chomp(data.http.my_ip.body)}/32"]
  target_tags   = ["webserver"]
}

resource "google_compute_address" "static" {
  name = "vm-public-address"
  project = var.project_name
  region = var.region
  depends_on = [ google_compute_firewall.firewall ]
}

resource "google_compute_disk" "default" {
  name  = "test-disk"
  type  = "pd-ssd"
  zone  = "${var.region}-c"
  image = "ubuntu-1604-xenial-v20210429"
  size = 64
  labels = {
    environment = "dev"
  }
  physical_block_size_bytes = 4096
}

resource "google_compute_instance" "default" {
  name         = "attached-disk-instance"
  machine_type = "e2-highmem-2"
  zone         = "${var.region}-c"
  tags         = ["externalssh","webserver"]

  boot_disk {
    source = google_compute_disk.default.name
  }
  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.static.address
    }
  }

  lifecycle {
    ignore_changes = [attached_disk]
  }
  metadata = {
    sshKeys = "${var.gce_ssh_user}:${file(var.gce_ssh_pub_key_file)}"
  }

  provisioner "file" {
    source      = "startupscript.sh"
    destination = "/tmp/startupscript.sh"
    connection {
      host        = google_compute_address.static.address
      type        = "ssh"
      user        = var.gce_ssh_user 
      timeout     = "500s"
      private_key = file(var.private_key_path)
   }
 }

  provisioner "file" {
    source      = "face-hunter.json"
    destination = "/root/face-hunter.json"
    connection {
      host        = google_compute_address.static.address
      type        = "ssh"
      user        = var.gce_ssh_user 
      timeout     = "500s"
      private_key = file(var.private_key_path)
   }
 }
  provisioner "remote-exec" {
    connection {
      host        = google_compute_address.static.address
      type        = "ssh"
      user        = var.gce_ssh_user
      timeout     = "500s"
      private_key = file(var.private_key_path)
   }
    inline = [
      "chmod a+x /tmp/startupscript.sh",
      "sed -i -e 's/\r$//' /tmp/startupscript.sh",
      "sudo /tmp/startupscript.sh"
   ]
 }
  depends_on = [google_compute_firewall.firewall, google_compute_firewall.webserverrule]
  service_account {
    scopes = ["compute-ro"]
  }
}

variable "project_name"{
  default = "face-hunter-319522"
}

variable "region"{
  default = "europe-west2"
}

variable "gce_ssh_user" {
  default = "root"
}

variable "gce_ssh_pub_key_file" {
  default = "./pub_key.pub"
}

variable "private_key_path"{
  default = "./pub_key"
}

data "http" "my_ip" {
   url = "https://checkip.amazonaws.com"
}

output "ip" {
 value = google_compute_address.static.address
}

