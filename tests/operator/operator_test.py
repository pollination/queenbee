import yaml
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest
from tests.base.folder_test import BaseFolderTest

from queenbee.plugin import Plugin

ASSET_FOLDER = 'tests/assets/plugins'


class TestIO(BaseIOTest):

    klass = Plugin

    asset_folder = ASSET_FOLDER


class TestValueError(BaseValueErrorTest):

    klass = Plugin

    asset_folder = ASSET_FOLDER


class TestFolder(BaseFolderTest):

    klass = Plugin

    asset_folder = ASSET_FOLDER
