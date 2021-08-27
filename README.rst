Face-Hunter: Multi-Modal Entity Linking
-----------------------------------------

Table of Contents
#################

.. contents::

How to setup on Google Cloud
##############

Follow these steps:

1. In the root folder create a ssh-key with an empty passphrase:

.. code-block::

    $  ssh-keygen -t rsa

2. Setup the cloud environment:

.. code-block::

    $  terraform init
    $  terraform plan
    $  terraform apply --auto-approve

3. Use the output IP-address to connect to the instance:

.. code-block::

    $ ssh-keygen -R IP_instance
    $ ssh -i pub_key root@IP_instance

4. Run the app:

.. code-block::

    $ sudo docker run -v /mnt/face-hunter-bucket:/root/FACE-HUNTER/face-hunter-bucket --privileged -it shaban2lesh/face-hunter /bin/bash
    $ cd root/FACE-HUNTER
    $ python cli.py ARGUMENTS

5. Destroy the instance when finished:

.. code-block::

    $ terraform destroy --auto-approve