import pytest
import os
import json
import yaml

from queenbee.base.parser import _import_dict_data


class BaseTestClass:

    test_folder = './tests/assets/temp'

    asset_folder = None

    klass = None

    def generate_test_file(self, name):
        return os.path.join(self.test_folder, name)

    def fixture_folders(self, path):

        if self.asset_folder is None:
            class_name = self.klass.__name__
            folder_path = os.path.join('tests/assets', class_name, path)
        else:
            folder_path = os.path.join(self.asset_folder, path)

        return [os.path.join(folder_path, folder) for folder in os.listdir(folder_path)]

    def fixture_files(self, path):

        if self.asset_folder is None:
            class_name = self.klass.__name__
            folder_path = os.path.join('tests/assets', class_name, path)
        else:
            folder_path = os.path.join(self.asset_folder, path)

        files = []

        # r=root, d=directories, f = files
        for r, d, f in os.walk(folder_path):
            for file in f:
                files.append(os.path.join(r, file))

        if files == []:
            # raise ValueError(f'No test files found at path: {folder_path}')
            pytest.skip(msg=f'No test files found at path: {folder_path}')

        return files

    def fixture_dicts(self, path):
        files = self.fixture_files(path)

        dicts = []

        for path in files:
            folder = os.path.dirname(path)

            ext = path.split('.')[-1].lower()
            if not ext in ('json', 'yml', 'yaml'):
                pytest.skip(
                    f'Invalid test asset file format (should be json, yml or yaml): {path}')

            if ext == 'json':
                with open(path) as inf:
                    dict_ = json.load(inf)
            else:
                with open(path) as inf:
                    dict_ = yaml.safe_load(inf.read())

            dict_ = _import_dict_data(dict_, folder)

            dicts.append(dict_)

        return dicts

    def fixture_instances(self, path, klass=None):
        paths = self.fixture_files(path)

        if klass is None:
            klass = self.klass

        instances = []

        for path in paths:
            try:
                instances.append(klass.from_file(path))
            except Exception as error:
                print(error)

        return instances
