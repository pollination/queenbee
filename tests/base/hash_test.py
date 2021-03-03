import pytest

from ._base import BaseTestClass

@pytest.mark.hash
class BaseHashTest(BaseTestClass):

    def pytest_generate_tests(self, metafunc):
        
        object_instances = self.fixture_instances('valid')

        if "instance" in metafunc.fixturenames:
            metafunc.parametrize("instance", object_instances)

    def test_generates_hash(self, instance):
        """Test to check for bug introduced in Pydantic 1.8"""
        
        assert instance.__hash__ is not None
