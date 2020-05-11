import yaml
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.operator.function import Function

ASSET_FOLDER = 'tests/assets/functions'

class TestIO(BaseIOTest):

    klass = Function

    asset_folder = ASSET_FOLDER

class TestValueError(BaseValueErrorTest):

    klass = Function

    asset_folder = ASSET_FOLDER
