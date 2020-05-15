Operators
=========


Schema
------

.. raw:: html

   <html open>

  <div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/nprogress/0.2.0/nprogress.min.js"></script>
    <!-- Nav/Toolbar -->
    <div class="btn-group" id="app-toolbar">
        <button id="sourceButton" type="button" class="btn btn-default"><span class="glyphicon glyphicon-align-left"> </span> Source</button>
        <button id="visualizeButton" type="button" class="btn btn-default"><span class="glyphicon glyphicon-eye-open"> </span> Visualize</button>
    </div>
    
    <!-- Editor -->
    <div id="editor"></div>
    
    <!-- JSV -->
    <div id="main-body"></div>
    
    <script>
      NProgress.start();
    </script>
    <script>
      jsonSchemaViewer(window, '/_static/schemas/operator-schema.json')
    </script>
    <script>
      NProgress.done();
    </script>
  </div>

.. raw:: html

   <html close>


You can find a link to the json schema definition `here </_static/schemas/operator-schema.json>`_

Examples
--------

Minimal
^^^^^^^
The minimal configuration for an operator can be found below. The keys indicated here are the ones
you **absolutely** have to fill in for this operator to be validated by Queenbee.

..  literalinclude:: ../../tests/assets/operators/valid/minimum.yaml
    :language: yaml


Fully Configured
^^^^^^^^^^^^^^^^
The operator below shows example values for every possible key in the Operator object.

..  literalinclude:: ../../tests/assets/operators/valid/full.yaml
    :language: yaml


Honeybee Radiance
^^^^^^^^^^^^^^^^
This is an example operator called ``honeybee-radiance``. This operator uses the ``honeybee-radiance`` CLI in a Docker container
which has radiance installed on it. Each function is templated with parameter inputs and explicitely indicates the artifacts (files)
it expects to find at a certain path.

.. Note::

  The ``appVersion`` matches the docker container release tag.

..  literalinclude:: ../../tests/assets/operators/valid/honeybee-radiance.yaml
    :language: yaml