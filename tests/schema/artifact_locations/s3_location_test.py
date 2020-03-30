import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.artifact_location import S3Location


class TestIO(BaseIOTest):

    klass = S3Location

class TestValueError(BaseValueErrorTest):

    klass = S3Location