import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.artifact_location import InputFolderLocation


class TestIO(BaseIOTest):

    klass = InputFolderLocation

class TestValueError(BaseValueErrorTest):

    klass = InputFolderLocation