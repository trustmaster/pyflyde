CLI usage
=========

Running Flyde graphs
--------------------

You can run a Flyde graph using the following command:

.. code-block:: console
    $ pyflyde run path/to/MyGraph.flyde

There is a shorter alias because `run` is the default command:

.. code-block:: console
    $ pyflyde path/to/MyGraph.flyde

Generating TypeScript definitions for Python modules
----------------------------------------------------

Use `gen` command to generate TypeScript definitions for Python modules every time you update them:

.. code-block:: console
    $ pyflyde gen path/to/MyModule.py
