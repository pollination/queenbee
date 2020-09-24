import pytest
import os
import yaml
import json
from ._base import BaseTestClass


@pytest.mark.folder
class BaseFolderTest(BaseTestClass):

    def pytest_generate_tests(self, metafunc):

        folders = self.class_folders()
        valid_instances = self.valid_instances()

        inputs = []

        for folder in folders:
            folder_name = os.path.basename(folder)
            matching_instances = [
                instance for instance in valid_instances if instance.metadata.name == folder_name]

            if len(matching_instances) == 1:
                inputs.append((folder, matching_instances[0]))

        if "folder" in metafunc.fixturenames:
            metafunc.parametrize("folder,instance", inputs, ids=[
                                 os.path.basename(input_tuple[0]) for input_tuple in inputs])

    def class_folders(self):
        return self.fixture_folders('folders')

    def valid_instances(self):
        return self.fixture_instances('valid')

    def test_from_folder(self, folder, instance):
        parsed_instance = self.klass.from_folder(folder)

        assert parsed_instance == instance
        assert parsed_instance.__hash__ == instance.__hash__
