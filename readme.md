# Face-Hunter
Team Project at the University of Mannheim

## Installation
 - Follow instructions of https://github.com/ageitgey/face_recognition 
   (Make sure that dlib and cmake are installed)
 - Install requirements `pip install requirements.txt`

 ## Provisioning GCP resources

In the root folder create ssh key using the following command

ssh-keygen -t rsa

when asked about the file name, insert "pub_key"
When asked for the passphrase, keep it empty

Use the commands below to start the script

 terraform init
 terraform plan
 terraform apply --auto-approve

 The commands output the IP_instance. We will use this IP to ssh to it using the command below. replace IP_instance with the actual numbers from the output

 ssh -i pub_key root@IP_instance

 if you get a warning like the one below
 @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
then use the command below and make sure to replace IP_instance with the actual IP you got from the output

ssh-keygen -R IP_instance

Then try to SSH again

If it works, use the command below to start running the app

sudo docker run -it shaban2lesh/face-hunter /bin/bash
cd root/FACE-HUNTER

and start running the commands

also install nano to be able to edit the code

apt-get install nano

then for example

nano cli.py

IMPORTANT!
When you finish don't forget to run the command below

terraform destroy --auto-approve

Enjoy!




