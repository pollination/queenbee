import pytest
import os
import json
import yaml

from queenbee.schema.parser import _import_dict_data

class BaseTestClass:
    
    test_folder ='./tests/assets/temp'

    klass = None

    def generate_test_file(self, name):
        return os.path.join(self.test_folder, name)

    def fixture_files(self, path):
        class_name = self.klass.__name__

        folder_path = os.path.join('tests/assets', class_name, path)

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
                pytest.skip(f'Invalid test asset file format (should be json, yml or yaml): {path}')

            if ext == 'json':
                with open(path) as inf:
                    dict_ = json.load(inf)
            else:
                with open(path) as inf:
                    dict_ = yaml.safe_load(inf.read())

            dict_ = _import_dict_data(dict_, folder)

            dicts.append(dict_)

        return dicts

    def fixture_instances(self, path):
        paths = self.fixture_files(path)

        instances = []

        for path in paths:
            instances.append(self.klass.from_file(path))

        return instances

            