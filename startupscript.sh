#!/bin/bash

sudo curl -sSL https://get.docker.com/ | sh
sudo usermod -aG docker `echo $USER`
sudo apt-get -y update
sudo apt-get install git
sudo docker pull shaban2lesh/face-hunter
#sudo docker run -it shaban2lesh/face-hunter /bin/bash