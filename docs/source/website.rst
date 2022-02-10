Website
=======

The website allows to query a generated knowledge graph from the `Face-Hunter <https://github.com/face-hunters/face-hunter/>`__
project.

It allows to search for scenes of entities or to write own SPARQL-queries and is build on `Angular <https://angular.io/>`__.
For usage follow the installation instructions on `Angular-Setup <https://angular.io/guide/setup-local/>`__.

The REST-API of the project must be started before the website:

1. Change directory and set the flask environment variable

.. code-block::

    $  cd api
    $  export FLASK_APP=api

2. Run the interface

.. code-block::

    $  flask run

How to run and debug the website locally
##################

In the dictionary of the website run:

.. code-block::

    $  ng serve

How to build for production
###########################

In the dictionary of the website run:

.. code-block::

    $  ng build

Afterwards the generated files can be found in a newly generated dist-folder.
