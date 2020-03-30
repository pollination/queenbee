import yaml
import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.arguments import WorkflowInputs


class TestIO(BaseIOTest):

    klass = WorkflowInputs

class TestValueError(BaseValueErrorTest):

    klass = WorkflowInputs