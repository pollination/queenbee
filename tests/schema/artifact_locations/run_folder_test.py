import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.artifact_location import RunFolderLocation


class TestIO(BaseIOTest):

    klass = RunFolderLocation

class TestValueError(BaseValueErrorTest):

    klass = RunFolderLocation