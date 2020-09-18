Create A New Repository
=======================

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
We will create a new queenbee repository in a folder called ``local-queenbee-repo``. To do
so run the following command::

    queenbee repo init local-queenbee-repo


This command will create the folders and initialize an empty ``index.json`` file. Here
is what the folder should look like::

    local-queenbee-repo
    ├── recipes
    ├── operators
    └── index.json


You will notice that the ``recipes`` and ``operators`` folders are empty. This is where
we will save the packaged recipes and operators. You will also notice that the ``index.json``
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
    └── index.json


Repository Indexing
-------------------
The repository index file (``index.json``) is the "brain" of the repository. This is where
package names, versions and other basic metadata is exposed for clients (ie: queenbee cli)
to search for packages and find their download paths.

The repository index is created by crawling the repository folders for packages and updating
the package information in the index as needed. Let's give it a try::

    queenbee repo index local-queenbee-repo

If you open your ``index.json`` file you will see that is has changed to something like this

..  note::
    Package name, version etc... will change according to the operator packaged in the
    previous step.

::

    {
    "generated": "2020-05-19T07:46:49.803320",
    "metadata": {
        "name": "local-queenbee-repo",
        "description": "A Queenbee package repository",
        "source": null,
        "operator_count": 1,
        "recipe_count": 0
    },
    "operator": {
        "energy-plus": [
        {
            "name": "energy-plus",
            "tag": "0.1.0",
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
            "digest": "bff20aae42e62aa084f0f08bf3833674e2bfccd0c6309f65848f089f402716f5",
            "slug": "local-queenbee-repo/energy-plus",
            "type": "operator"
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

    queenbee repo index local-queenbee-repo --force


You can **remove** a package version from an index by deleting the package file from
the folder and then running the following command::

    queenbee repo index local-queenbee-repo --new
