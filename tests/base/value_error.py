import pytest
import os
import yaml
import json
from ._base import BaseTestClass


@pytest.mark.err
class BaseValueErrorTest(BaseTestClass):

    def pytest_generate_tests(self, metafunc):

        invalid_files = self.invalid_files()

        parametrized = []

        for f in invalid_files:
            parametrized.append((f, f))

        if 'invalid_file' in metafunc.fixturenames and 'error_message' in metafunc.fixturenames:
            
            metafunc.parametrize(
                'invalid_file, error_message',
                parametrized,
                indirect=['error_message'],
                ids=invalid_files,
            )

        if 'invalid_file' in metafunc.fixturenames and 'error_message' not in metafunc.fixturenames:
            
            metafunc.parametrize(
                'invalid_file',
                invalid_files,
                ids=invalid_files,
            )


    @staticmethod
    def readable_extension_check(file_path):
        _, file_extension = os.path.splitext(file_path)
        return file_extension in ['.json', '.yml', '.yaml']

    def invalid_files(self):
        all_files = self.fixture_files('invalid')
        return list(filter(
            lambda x: self.readable_extension_check(x),
            all_files
        ))

    @pytest.fixture(scope='function')
    def error_message(self, request):
        file_path, _ = os.path.splitext(request.param)
        error_message_path = '.'.join([file_path, 'error'])
        try:
            with open(error_message_path, 'r') as f:
                return f.read()
        except:
            pytest.skip(f'Cannot read value error message at path: {error_message_path}')

    def test_raise_value_error(self, invalid_file):
        with pytest.raises(ValueError):
            self.klass.from_file(invalid_file)

    def test_value_error_message(self, invalid_file, error_message):
        with pytest.raises(ValueError, match=error_message):
            self.klass.from_file(invalid_file)
