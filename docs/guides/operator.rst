Create A New Operator
=====================

In this section we will walk you through how to create a new operator from an existing Command Line Interface (CLI) tool. We will create a folder to save our
operator definition, write the operator package metadata and define a few functions exposed by the operator.

We will be creating an Operator that uses EnergyPlus. This Operator will transform commands provided in the `examples <https://github.com/NREL/EnergyPlus/blob/370d5b8f4d8a27a80d9b6ed21b1fa7a989f75dc1/doc/running-energyplus-from-command-line.md#examples>`_ 
section of the CLI documentation into Queenbee Operator Functions.

Getting Started
---------------
First we need to create a new Operator folder. We will do so using the Queenbee CLI tool::

  queenbee operator new energy-plus


This will create a folder called ``energy-plus`` with a pre-populated template. Have a look at the
default template by opening the ``energy-plus`` folder with your code editor.

Folder Structure
----------------
When you open the folder in your code editor you will notice their is a folder called ``functions``,
a file called ``config.yaml`` and another file called ``operator.yaml``::

    energy-plus
    ├── functions           # Contains all the functions the operator can run
    │   └── say-hi.yaml     # A function that executes a `say-hi` command
    ├── config.yaml         # Configuration information to execute this function locally or using Docker
    └── operator.yaml       # The Operator metadata information (name, version etc...)



Configuration
-------------
The ``config.yaml`` file contains information to indicate what underlying software should execute
the operator's functions. We will be focusing on the ``docker`` configuration.

You can check the full schema definition for an Operator Config `here <../_static/redoc-operator.html#tag/config_model>`_

Docker Config
^^^^^^^^^^^^^
The Docker configuration tells the workflow execution engine which container to use when executing a Function
from this Operator. It will also indicate what path within the folder each artifact (file or folder) should be
loaded to.

Our energy-plus operator will use `a container image produced by NREL <https://hub.docker.com/r/nrel/energyplus>`_.
We want to use a specific version of energyplus (``v9.0.1``), therefore the name of the container image we want to use
is ``nrel/energyplus:9.0.1``.


The container image documentation explains that::

  To run EnergyPlus you should either mount your directory into the container or create a dependent container where you call ADD . /var/simdata.

  To mount the local folder and run EnergyPlus (on Linux only) make sure that your simulation directory is the current directory and run:

  > docker run -it --rm -v $(pwd):/var/simdata nrel/energyplus EnergyPlus

This means that when the Docker container is run, the command is run from the ``/var/simdata`` directory. This
is what we call the Working Directory or ``wordir`` for short.

Overwrite the contents of the ``config.yaml`` file with the YAML code block below:

..  literalinclude:: ../../tests/assets/operators/folders/energy-plus/config.yaml
    :language: yaml


Operator.yaml
-------------
This file contains the metadata information that defines your Operator. You can compare this to the
``package.json`` for Node, ``setup.py`` for Python or ``<package-name>.sln`` for C#.

The file currently contains name and version information:

.. code-block:: yaml

  name: energy-plus
  version: 0.1.0

These are the two mandatory fields for this file. You can view a full list of other available 
fields `here <../_static/redoc-operator.html#tag/metadata_model>`_.

We will be adding a few more fields for demonstration purposes. Overwrite the contents of
``operator.yaml`` with the YAML code block below.

..  literalinclude:: ../../tests/assets/operators/folders/energy-plus/operator.yaml
    :language: yaml


Your First Function
-------------------
We are now finally ready to write a Function. Functions are the key ingredients of an Operator. A Function
defines a parametrized command run in a terminal. You can refer to the 
`function schema definition  <../_static/redoc-operator.html#tag/function_model>`_ to understand the components of a function.


We listed some function we wanted to create based on examples provided by the EneryPlus documentation. 

We will start by creating a function that takes a weather file and an ``idf`` file as inputs, runs an energyplus simulation
and outputs a folder with all the EnergyPlus output files. Delete the ``say-hi.yaml`` file in your ``functions`` folder.
Now create a new file called ``run-simulation.yaml`` in the ``functions`` folder and copy the following YAML code block:

..  note::
    The ``path`` of the input and output artifacts correspond to file or folder paths indicated by the
    ``command``. The ``weather.epw`` and ``input.idf`` are explicitly called and the ``outputs`` directory is
    created by specifying ``-d outputs`` in the command.

..  literalinclude:: ../../tests/assets/operators/folders/energy-plus/functions/run-simulation.yaml
    :language: yaml


Your folder should now look something like this::

    energy-plus
    ├── functions
    │   └── run-simulation.yaml
    ├── config.yaml
    └── operator.yaml


Packaging and Sharing
---------------------
You can package an operator by running the following command::

  queenbee operator package energy-plus


You should see a file called ``energy-plus-0.1.0.tgz`` appear in your local
directory. This is a packaged Operator file which can be saved in a Queenbee
Repository to share with others or be used in a Recipe.

You should go to the `Repository Guide <repository.html>`_ section to understand
how Operators are packaged and shared. 


Using Operators
---------------
You should move to the `Recipe Guide <recipe.html>`_ section to understand how
Operators are used by recipes.
