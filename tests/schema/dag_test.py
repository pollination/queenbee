import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.dag import DAG


class TestIO(BaseIOTest):

    klass = DAG

class TestValueError(BaseValueErrorTest):

    klass = DAG
