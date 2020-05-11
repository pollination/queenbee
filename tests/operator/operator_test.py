import yaml
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest
from tests.base.folder_test import BaseFolderTest

from queenbee.operator import Operator

ASSET_FOLDER = 'tests/assets/operators'

class TestIO(BaseIOTest):

    klass = Operator

    asset_folder = ASSET_FOLDER

class TestValueError(BaseValueErrorTest):

    klass = Operator

    asset_folder = ASSET_FOLDER

class TestFolder(BaseFolderTest):

    klass = Operator

    asset_folder = ASSET_FOLDER
