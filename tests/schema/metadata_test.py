from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.metadata import MetaData

class TestIO(BaseIOTest):

    klass = MetaData

class TestValueError(BaseValueErrorTest):

    klass = MetaData