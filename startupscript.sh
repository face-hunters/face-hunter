#!/bin/bash

sudo curl -sSL https://get.docker.com/ | sh
sudo usermod -aG docker `echo $USER`
sudo apt-get -y update
sudo apt-get -y install git


echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
apt-get --yes --force-yes install apt-transport-https ca-certificates gnupg
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
apt-get -y update && apt-get --yes --force-yes install google-cloud-sdk

export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
apt-get -y update
apt-get --yes --force-yes install gcsfuse

export GOOGLE_APPLICATION_CREDENTIALS=/root/face-hunter.json
mkdir /mnt/face-hunter-bucket
gcsfuse face-hunter-bucket /mnt/face-hunter-bucket

sudo docker pull shaban2lesh/face-hunter
# sudo docker run -v /mnt/face-hunter-bucket:/root/FACE-HUNTER/face-hunter-bucket --privileged -it shaban2lesh/face-hunter /bin/bash