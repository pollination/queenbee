import yaml
import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from queenbee.schema.arguments import Arguments


class TestIO(BaseIOTest):

    klass = Arguments


class TestValueError(BaseValueErrorTest):

    klass = Arguments


def test_get_param_value():
    args = Arguments.from_file('./tests/assets/Arguments/valid/complete.yaml')

    with pytest.raises(ValueError):
        args.get_parameter_value('worker')

    assert args.get_parameter_value('sensor-count') == 250


def test_get_artifact_value():
    args = Arguments.from_file('./tests/assets/Arguments/valid/complete.yaml')

    with pytest.raises(ValueError):
        args.get_artifact_value('model-source')

    assert args.get_artifact_value('input-grid-folder') == 'asset/grid'
