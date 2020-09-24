import pytest
import os
import yaml
import json
from ._base import BaseTestClass


@pytest.mark.io
class BaseIOTest(BaseTestClass):

    def pytest_generate_tests(self, metafunc):

        valid_files = self.valid_files()
        valid_dicts = self.valid_dicts()
        # valid_instances = self.valid_instances()

        # if "valid_instance" in metafunc.fixturenames:
        #     metafunc.parametrize("valid_instance", valid_instances, ids=valid_files)

        if "valid_dict" in metafunc.fixturenames:
            metafunc.parametrize("valid_dict", valid_dicts, ids=valid_files)

    def valid_files(self):
        return self.fixture_files('valid')

    def valid_dicts(self):
        return self.fixture_dicts('valid')

    def valid_instances(self):
        return self.fixture_instances('valid')

    def test_from_json(self, valid_dict):
        test_file_path = self.generate_test_file('valid.json')

        with open(test_file_path, 'w') as f:
            json.dump(valid_dict, f)

        instance = self.klass.from_file(test_file_path)

        assert instance == self.klass.parse_obj(valid_dict)

    def test_from_yaml(self, valid_dict):
        test_file_path = self.generate_test_file('valid.yaml')

        with open(test_file_path, 'w') as f:
            yaml.dump(valid_dict, f)

        instance = self.klass.from_file(test_file_path)

        assert instance == self.klass.parse_obj(valid_dict)

    def test_to_yaml(self, valid_dict):
        valid_instance = self.klass.parse_obj(valid_dict)

        loc_file = self.generate_test_file('valid.yaml')

        valid_instance.to_yaml(loc_file)

        with open(loc_file) as inf:
            obj = yaml.safe_load(inf.read())

        assert obj == valid_instance.to_dict()
        assert self.klass.from_file(
            loc_file).__hash__ == valid_instance.__hash__

    def test_to_json(self, valid_dict):
        valid_instance = self.klass.parse_obj(valid_dict)

        loc_file = self.generate_test_file('valid.json')

        valid_instance.to_json(loc_file)

        with open(loc_file) as inf:
            obj = json.load(inf)

        assert obj == valid_instance.to_dict()
        assert self.klass.from_file(
            loc_file).__hash__ == valid_instance.__hash__
