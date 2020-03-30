import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.artifact_location import HTTPLocation


class TestIO(BaseIOTest):

    klass = HTTPLocation

class TestValueError(BaseValueErrorTest):

    klass = HTTPLocation