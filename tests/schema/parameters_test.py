from queenbee.schema.arguments import Parameter
import pytest


def test_wrong_referenced_parameters():
    with pytest.raises(ValueError):
        Parameter(name='param', value='"{{workflow.wrong-input}}"')

    with pytest.raises(ValueError):
        Parameter(name='param', value='"{{workflow.inputs.parameters}}"')

    with pytest.raises(ValueError):
        Parameter(name='param', value='"{{workflow.inputs.parameters.name.value}}"')


def test_referenced_parameters():
    par = Parameter(name='new-param', value='"{{workflow.inputs.parameters.name}}"')
    assert par.ref_vars == {'value': ['workflow.inputs.parameters.name']}


def test_referenced_parameters_path():
    par = Parameter(name='new-param', path='"{{workflow.inputs.parameters.name}}"')
    assert par.ref_vars == {'path': ['workflow.inputs.parameters.name']}


def test_value_path_clash():
    with pytest.raises(ValueError):
        Parameter(name='new-param', value=1, path='path to file')


def test_current_value():
    par = Parameter(name='new-param', value=20)
    assert par.current_value == 20


def test_current_value_path():
    par = Parameter(name='new-param', path='path to file')
    assert par.current_value == 'path to file'
