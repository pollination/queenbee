Create and Manage a Repository
==============================

Queenbee repositories are essential to store and share Operators and Recipes that can be executed as Workflows.

A Repository is a folder that consists of an ``index.json`` index file and a series of packaged Operators and Recipes.
It is used to manage Recipe dependencies (which can be Operators or other Recipes).

In this section we will show you how to create a repository folder on your machine. You can then use this
folder to develop multiple Operators and Recipes that depend on each other.

Getting Started
---------------
We will need an Operator stored in folder for this tutorial. You can follow the `Operator Guide <operator.html>`_
if you do not have an operator folder at hand.

Folder Structure
----------------
We will create a new Queenbee repository in a folder called ``local-queenbee-repo``. To do
so run the following command::

    queenbee repository init local-queenbee-repo


This command will create the folders and initialize an empty ``index.json`` file. Here
is what the folder should look like::

    local-queenbee-repo
    ├── recipes
    ├── workflows
    └── index.json


You will notice that the ``recipes`` and ``workflows`` folders are empty. This is where
we will save the packaged recipes and workflows. You will also notice that the ``index.json``
file also doesn't show much information yet::

    {
        "generated": "2020-05-19T07:32:02.599910",
        "operator": {},
        "recipe": {}
    }

Adding Packages
---------------
Let's add some packages to our repository. To do so we will package the Operator we 
created in the `Operator Guide <operator.html>`_ (or any other operator you might have 
created). ::

    queenbee operator package path/to/operator --destination local-queenbee-repo/operators

If you are using the Operator we created in the `Operator Guide <operator.html>`_ the
path/to/operator is the ``energy-plus`` Operator folder.

You should now see a new file has been added to your repository.

..  note..
    The ``index.json`` file has not changed yet. This is because an index is only updated
    when explicitly asked to.

::

    local-queenbee-repo
    ├── operators
    │   └── energy-plus-0.1.0.tgz # Name will change if you used another operator
    ├── recipes
    ├── workflows
    └── index.json


Repository Indexing
-------------------
The repository index file (``index.json``) is the "brain" of the repository. This is where
package names, versions and other basic metadata is exposed for clients (ie: queenbee cli)
to search for packages and find their download paths.

The repository index is created by crawling the repository folders for packages and updating
the package information in the index as needed. Let's give it a try::

    queenbee repository index local-queenbee-repo

If you open your ``index.json`` file you will see that is has changed to something like this

..  note::
    Package name, version etc... will change according to the operator packaged in the
    previous step.

::

    {
    "generated": "2020-05-19T07:46:49.803320",
    "operator": {
        "energy-plus": [
        {
            "name": "energy-plus",
            "version": "0.1.0",
            "app_version": "9.0.1",
            "keywords": [
                "energyplus"
            ],
            "maintainers": null,
            "home": "https://energyplus.net",
            "sources": [
                "https://github.com/nrel/energyplus"
            ],
            "icon": "https://energyplus.net/sites/default/files/eplus_logo.png",
            "deprecated": null,
            "description": "An operator to run EnergyPlus functions",
            "url": "operators/energy-plus-0.1.0.tgz",
            "created": "2020-05-19T07:42:20.496003",
            "digest": "bff20aae42e62aa084f0f08bf3833674e2bfccd0c6309f65848f089f402716f5"
        }
        ]
    },
    "recipe": {}
    }

There are a few interesting things going on here:

- The operator package is nested under the ``operator`` key
- The operator name key points to a list of **Operator Versions**. In this example the key is ``energy-plus``.
- The **Operator Version** ``url`` key points to the package file relative to the ``index.json`` file
- A ``digest`` is generated for each **Operator Version** This is used to handle ``version`` overwrites


Using a Local Repository
------------------------
The main purpose of a Queenbee Repository is to be available online so that others can
access your great work on their machine. However it can be useful to use a repository 
locally for local development.

This can be useful when working on a new Operator that must be tested against a few new 
Recipes. It can also be helpful when upgrading an Operator and wanting to run backwards 
compatibility checks against multiple existing Recipes.

To work with a local repository you must expose it as a local server on your machine::

    queenbee repository serve local-queenbee-repo


You should now be able to view your ``index.json`` file from your browser at the
following address `http://localhost:8000/index.json <http://localhost:8000/index.json>`_.

..  note::
    If the port 8000 is not available you can change the port using ``--port`` option.
    For instance ``queenbee repository serve local-queenbee-repo --port 8080`` will view
    your ``index.json`` file at the following address:
    `http://localhost:8080/index.json <http://localhost:8080/index.json>`_.

If we write a Recipe that depends on the ``energy-plus`` operator used in the examples above
we can write the ``dependencies.yaml`` file as follows::

    dependencies:
    - type: operator
      name: energy-plus
      version: 0.1.0
      source: http://localhost:8000


Overwriting/Deleting Existing Package Versions
----------------------------------------------
By default Queenbee makes it difficult to overwrite existing package
versions. This is to avoid causing issues to any downstream Recipes using
your package. 

..  warning::
    Don't read any further unless you know what you are doing 
    and accept the never ending slew of emails you will receive
    from angry people after overwriting or deleting a package version.

You can **force** the repository index process to overwrite any new packages added to
the index::

    queenbee repository index local-queenbee-repo --force


You can **remove** a package version from an index by deleting the package file from
the folder and then running the following command::

    queenbee repository index local-queenbee-repo --new
