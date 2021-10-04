Face-Hunter: Multi-Modal Entity Linking
-----------------------------------------

.. image:: https://img.shields.io/github/stars/face-hunters/face-hunter
.. image:: https://github.com/face-hunters/face-hunter/actions/workflows/test.yml/badge.svg
.. image:: https://github.com/face-hunters/face-hunter/actions/workflows/gh-release.yaml/badge.svg

A project that allows to create and query a knowledge graph of videos and their DBpedia and Wikidata entities.

Table of Contents
#################

.. contents::

Description
###########

Entity linking allows leveraging information about named entities from a knowledge base.

This work shows that face recognition methods can be used to identify entities in videos such that users can formulate
detailed queries with information from DBpedia and Wikidata. The focus of this project lies on
videos from YouTube.

To address this issue we use publicity available thumbnails from DBpedia and Wikidata to create face-embeddings
for a large number of celebrities using the `Deepface <https://github.com/serengil/deepface/>`__ library.
Additionally, our project allows to scrape material from Google Images to represent entities in different scenes.
Experiments have shown that recognition based on approximate k-nearest neighbors leads to the best balance
between accuracy and runtime. Finally, the detected entities are used to build a knowledge graph based on the paper
`VidOnt: a core reference ontology for reasoning over video scenes <https://www.tandfonline.com/doi/full/10.1080/24751839.2018.1437696/>`__ which represents
the links between videos, entities and timestamps. This gives the advantage of queries which include co-occurrences of actors
or other video-related information.
The figure below illustrates the structure of the generated graphs.

.. image:: https://i.ibb.co/Q6Fxk0s/Untitled-Diagram-drawio.png

Using the `YouTube Faces Database <https://www.cs.tau.ac.il/~wolf/ytfaces/>`__ and
`YouTube Celebrities Face Tracking and Recognition Dataset <http://seqamlab.com/youtube-celebrities-face-tracking-and-recognition-dataset/>`__
we achieved an accuracy of 0.603 and 0.64 respectively. Scraping additional images improved the results to 0.86 and 0.826.
Evaluation steps for the `IMDb-Face <https://github.com/fwang91/IMDb-Face/>`__ and `IMDb-Wiki <https://data.vision.ee.ethz.ch/cvl/rrothe/imdb-wiki/>`__
are implemented and allow future performance tests.

How to setup on Google Cloud
############################

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

    $ sudo docker run -v /mnt/face-hunter-bucket:/root/FACE-HUNTER/face-hunter-bucket --privileged -it facehunters/face-hunter /bin/bash
    $ cd root/FACE-HUNTER
    $ python cli.py ARGUMENTS

5. Destroy the instance when finished:

.. code-block::

    $ terraform destroy --auto-approve

How to use
##########

The module can be imported and used directly in Python or by accessing the command line interface.

A detailed documentation can be found `here <https://face-hunter.readthedocs.io/>`__.

Credits
#######

This project started at the end of March 2021 as a Team Project at the University of Mannheim.
The team consists of:

* `Ali Shaban <https://github.com/Alishaba/>`__
* `Bo Tong <https://github.com/bbbbtong/>`__
* `Honglin Li <https://github.com/Honglin-Li/>`__
* `Tim Grams <https://github.com/timg339/>`__

License
#######

This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.

