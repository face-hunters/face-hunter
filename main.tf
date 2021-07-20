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
  source_ranges = [var.my_ip] # Not So Secure. Limit the Source Range
  target_tags   = ["externalssh"]
}

resource "google_compute_firewall" "webserverrule" {
  name    = "gritfy-webserver"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["80","443"]
  }
  source_ranges = [var.my_ip] # Not So Secure. Limit the Source Range
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
  image = "debian-9-stretch-v20200805"
  labels = {
    environment = "dev"
  }
  physical_block_size_bytes = 4096
}

resource "google_compute_instance" "default" {
  name         = "attached-disk-instance"
  machine_type = "e2-medium"
  zone         = "${var.region}-c"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1404-trusty-v20160602"
    }
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
      # username of the instance would vary for each account refer the OS Login in GCP documentation
      user        = var.gce_ssh_user 
      timeout     = "500s"
      private_key = file(var.private_key_path)
   }
 }
  provisioner "remote-exec" {
    connection {
      host        = google_compute_address.static.address
      type        = "ssh"
      # username of the instance would vary for each account refer the OS Login in GCP documentation
      user        = var.gce_ssh_user
      timeout     = "500s"
      # private_key being used to connect to the VM. ( the public key was copied earlier using metadata )
      private_key = file(var.private_key_path)
   }
   # Commands to be executed as the instance gets ready.
   # set execution permission and start the script
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

resource "google_compute_attached_disk" "default" {
  disk     = google_compute_disk.default.id
  instance = google_compute_instance.default.id
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
  default = "pub_key.pub"
}

variable "private_key_path"{
  default = "pub_key"
}

variable "my_ip"{
  default = "88.76.252.218/32"
}

output "ip" {
 value = google_compute_address.static.address#google_compute_instance.default.network_interface.0.access_config.0.nat_ip
}