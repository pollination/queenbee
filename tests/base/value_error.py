from pydantic_core import ValidationError
import pytest
import os
import yaml
import json
import re
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
            pytest.skip(
                f'Cannot read value error message at path: {error_message_path}')

    def test_raise_value_error(self, invalid_file):
        with pytest.raises(ValueError):
            self.klass.from_file(invalid_file)

    def test_value_error_message(self, invalid_file, error_message):
        # 1. Prepare the Regex
        
        # Strip the legacy (type=...) suffix
        pattern = re.sub(r'\\\(type=.*\)$', '', error_message.strip())
        
        # FIX: Remove the greedy "match everything" prefix `((.|\n)*)`. 
        # Since we use re.search(), we don't need to explicitly match the start of the string.
        # We also strip leading whitespace to ignore the old indentation.
        pattern = pattern.replace(r"((.|\n)*)", "").strip()

        # 2. Catch ValueError
        with pytest.raises(ValueError) as excinfo:
            self.klass.from_file(invalid_file)
            
        # 3. Unwrap Pydantic error
        wrapped_error = excinfo.value.args[0]
        
        if hasattr(wrapped_error, 'errors'):
            # Extract plain messages (e.g., "Assertion failed, Cannot use template...")
            actual_messages = [e['msg'] for e in wrapped_error.errors()]
            
            # Check if the cleaned pattern exists inside any of the error messages
            match_found = any(re.search(pattern, msg) for msg in actual_messages)
            
            assert match_found, (
                f"Regex pattern '{pattern}' did not match any error messages.\n"
                f"Found messages: {actual_messages}"
            )
        else:
            # Fallback for generic ValueErrors
            actual_error = str(excinfo.value)
            assert re.search(pattern, actual_error), \
                f"Regex '{pattern}' not found in error '{actual_error}'"
