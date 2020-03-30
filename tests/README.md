# Tests

The `tests` folder contains unit tests, schema object assets to test with and reusable test classes.

## Unit Tests

All unit tests can be found in the `schema` folder. The aim of these tests is to check object IO behavior when reading/writing/parsing yaml/json/dicts. The unit tests should also verify any other behavior such as workflow hydration.

## Reusable Test Classes

For the sake of readability and dryness some reusable test classes have been created in the `base` folder. These test classes generate IO and Value Error tests based of the assets folder strucutre and a given class. In order to use these test classes you must import them into your unit test and use them as the parent class for a queenbee schema class specific test suite.

Here is an example of importing the IO and Value Error test classes to implement IO tests on the DAG class object:

`tests/schema/dag_test.py`

```python
import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.dag import DAG


class TestIO(BaseIOTest):

    klass = DAG

class TestValueError(BaseValueErrorTest):

    klass = DAG

```


## Assets

Assets are valid or invalid schema objects used to check the behavior of the Queenbee schema code base. They are organised by class name (in PascalCase). Any schema object in the `valid` subfolder should be readable by the class indicated by the parent folder name and return no errors. Objects in the `invalid` folder should return errors when parsed by the class indicated by the parent folder name.

For `invalid` folders there is an option to add a file with the same name as the incorrect object but with an `.error` file extension. This file will contain the expected error message from reading the incorrect file it is named after. Here is an example:

`tests/asets/DAG/invalid/flow_invalid_loop.yaml`
```yaml
name: arrival
target: walk-in
tasks:
- name: say-hi
  template: say-hi
- name: step-in
  template: step-in
  arguments:
    parameters:
    - name: step-count
      value: "{{workflow.inputs.parameters.step-count}}"
    - name: shake-hand
      value: "{{workflow.inputs.parameters.shake-hand}}"
  dependencies:
    - say-hi
- name: take-off-shoes
  template: take-off-shoes
  dependencies:
    - say-hi
- name: walk-in
  template: walking
  loop: "{{tasks.step-in.outputs.parameters.step-count}}"
  dependencies:
  - take-off-shoes
  - step-in
fail_fast: true
```

`tests/assets/DAG/invalid/flow_invalid_loop.error`
```
loop.*no argument
```