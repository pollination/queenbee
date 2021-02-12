Create A New Recipe
===================

In this section we will walk you through how to create a new Recipe.

..  warning::
    This section is not complete yet. Please refer to the
    `Recipe Schema </schemas/recipes.html>`_ section for now.

Getting Started
---------------

A Recipe defines a set of Tasks which are combined in a directed acyclic
graph (DAG). The edges of this graph correspond to the path that an input takes
to a Task. The outputs of a Task can be passed as inputs to subsequent Tasks.
As the graph is acyclic, a Task may not pass its output to any Task
that is at an equal or earlier stage in the Recipe.

This graph can be thought of as a program's `call graph <https://en.wikipedia.org/wiki/Call_graph>`_, but one that can call functions
written in arbitrary languages executed on an arbitrary runtime rather than simply being executed by ``python`` or ``node`` or compiled into an ELF and run on a compatible OS.

As such, the outputs of one Task that are sent to another Task can be thought of as a kind
of file-based inter-process communication. Provided that the first Task can output a filetype
that the second Task can parse, the implementation is of no concern. At least, at the level of a Recipe.

Finally, it is important to note that a Task in a Recipe could be another
DAG made of many individual Tasks. Thus, graphs can be nested inside one another
to isolate arbitrary levels of complexity in a manageable way.

Similar to the plugin creation documentation, the first step is to use
``queenbee`` to create a recipe scaffold:

.. code-block:: console
    $ queenbee recipe new my-recipe

This will create a directory ``my-recipe`` in your current working directory.

Folder Structure
----------------

The structure of the created folder should look something like this::

    my-recipe
    ├── flow
    │   └── main.yaml
    ├── dependencies.yaml
    ├── LICENSE
    ├── package.yaml
    └── README.md

Metadata Configuration
----------------------

The recipe's metadata is defined by the ``package.yaml`` file. It is composed
of a ``MetaData`` type with multiple nullable fields. If you are familiar with
the ``npm`` ecosystem, you can think of this as an analogue to the
non-executable fields of ``package.json`` such as ``name``, ``version``,
``description``, etc.

* **annotations**: A dictionary of arbitrary (key, value) pairs that can be
    consumed by consumers of the recipe.
* **name**: The name of the recipe.
* **tag**: The tag of the recipe.
* **app_version**: The version of the application.
* **keywords**: A list of strings that are related to the package.
* **maintainers**: A list of ``Maintainer`` objects that describe the contact
    information of the people responsible for the recipe (you, in this case).
* **home**: ?
* **sources**: ?
* **icon**: A publicly-accessible URI to give the recipe a friendly face.
* **deprecated**: Whether or not the recipe is in active development.
* **description**: A textual description, analogous to a README.
* **license**: A valid `SPDX Identifier <https://spdx.org/licenses/>`_ which
    corresponds to the text in the ``LICENSE`` file.

Dependencies
------------

The dependencies are specified in the ``dependencies.yaml`` file. Each entry in
the ``dependencies`` array should point to a valid, packaged Plugin at a local
path (such as the result from the ``Create a New Recipe`` documentation) or
hosted on a publicly-available package server.

Flow
----

The ``flow/`` directory contains the YAML definitions of the DAGs of the recipe
as YAML files. At a minimum, the directory must contain a ``main.yaml`` which
is, surprisingly, the main graph.

DAG Tasks
---------

As mentioned above, a Task can itself be a DAG. This both allows comlpex graphs
to be reused inside other graphs and allows isolating related Tasks into a logical unit.

Referencing Outputs to Inputs
-----------------------------

?


Artifact Path Context Resolution
--------------------------------

?

Working With Loops
------------------

?
