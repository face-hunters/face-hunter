Python Interface
================

    You can import the Hunter class into your own projects using the following lines of code:

            >>> from src.hunter import Hunter
            >>> hunter = Hunter("https://www.youtube.com/watch?v=DbpdIEs2Xig").fit()

    Afterwards you can either use the class to get a list of entities in the video:

            >>> hunter.recognize()

    to link the entities to a knowledge graph:

            >>> hunter.link()

    or to search for scenes of entities in an existing database:

            >>> hunter.search("Adam Sandler")

.. autoclass:: src.hunter.Hunter
    :members: