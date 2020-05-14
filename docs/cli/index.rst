CLI Docs
========

Installation
------------

You can install the `queenbee` cli tool using the following command::

   pip install -u queenbee[cli]

.. note::
   You might need to add "\\" to escape the "[]" brackets on unix based systems::

      pip install -u queenbee\[cli\]

CLI
----
.. click:: queenbee.cli:main
   :prog: queenbee


Commands
--------

.. toctree::
   :maxdepth: 1

   operator
   recipe
   repository