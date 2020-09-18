Queenbee Schemas
================

There are two main schemas that users should concern themselves with when using Queenbee. The **Operator** schema and the **Recipe** schema.
These two types of objects are written/created by users to express business logic to be executed.

There is an additional schema called a **Workflow**. Users supply **input arguments** and a **recipe** to a workflow executor, which will then
create and manage a Workflow object. The resulting Workflow object is **read only** and is used to monitor the execution and output data from the
workflow executor.

.. toctree::
   :maxdepth: 1
   :caption: Schema Definitions and Examples:

   operators
   recipes
   repository
   workflows