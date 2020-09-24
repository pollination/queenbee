from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest
from tests.base.folder_test import BaseFolderTest

from queenbee.recipe import Recipe

ASSET_FOLDER = 'tests/assets/recipes'


class TestIO(BaseIOTest):

    klass = Recipe

    asset_folder = ASSET_FOLDER


class TestValueError(BaseValueErrorTest):

    klass = Recipe

    asset_folder = ASSET_FOLDER


class TestFolder(BaseFolderTest):

    klass = Recipe

    asset_folder = ASSET_FOLDER
