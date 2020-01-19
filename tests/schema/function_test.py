from queenbee.schema.function import Function
import pytest


def test_load_function():
    fp = './tests/assets/function.yaml'
    Function.from_file(fp)


def test_load_function_with_int_input():
    fp = './tests/assets/function_int_input.yaml'
    fn = Function.from_file(fp)
    assert fn.inputs.parameters[1].value == 250


def test_load_input_referenced():
    fp = './tests/assets/function_referenced_input.yaml'
    msg = r'There is at least one referenced variable in inputs:'
    with pytest.raises(ValueError, match=msg):
        Function.from_file(fp)


def test_load_illegal_input():
    fp = './tests/assets/function_illegal_input.yaml'

    with pytest.raises(ValueError):
        Function.from_file(fp)


def test_load_workflow_input():
    fp = './tests/assets/function_workflow_reference.yaml'
    with pytest.raises(ValueError):
        Function.from_file(fp)
