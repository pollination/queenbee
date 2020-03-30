import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.function import Function

class TestIO(BaseIOTest):

    klass = Function

class TestValueError(BaseValueErrorTest):

    klass = Function

