from queenbee.schema.arguments import Arguments, Parameter, Artifact
import yaml
import pytest


def test_load_arguments():
    args = Arguments.from_file('./tests/assets/arguments.yaml')

    # check parameter
    parameter = args.parameters[0]
    assert isinstance(parameter, Parameter)
    assert parameter.name == 'grid-name'
    assert parameter.value == 'grid'

    # check artifact
    artifact = args.artifacts[0]
    assert isinstance(artifact, Artifact)
    assert artifact.name == 'input-grid-folder'
    assert artifact.location == 'model-source'
    assert artifact.path == 'asset/grid'

def test_load_params_only_arguments():
    args = Arguments.from_file('./tests/assets/parameters.yaml')

    # check parameter
    parameter = args.parameters[0]
    assert isinstance(parameter, Parameter)
    assert parameter.name == 'grid-name'
    assert parameter.value == 'grid'


def test_create_arguments():
    args_dict = {
        'parameters': [{'name': 'worker', 'value': 1}],
        'artifacts': [
            {'name': 'project-folder', 'source_path': '.',
            'path': 'project', 'location': 'project-folder'}
        ]
    }

    args = Arguments.parse_obj(args_dict)

    args_file = './tests/assets/temp/arguments.yaml'
    args.to_yaml(args_file)

    # parse the yaml file and compare the two
    with open(args_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == args.to_dict()


def test_load_duplicate_name():
    with pytest.raises(ValueError):
        Arguments.from_file('./tests/assets/arguments_dup_name.yaml')


def test_get_param_value():
    args = Arguments.from_file('./tests/assets/arguments.yaml')

    with pytest.raises(ValueError):
        args.get_parameter_value('worker')

    assert args.get_parameter_value('sensor-count') == 250


def test_get_artifact_value():
    args = Arguments.from_file('./tests/assets/arguments.yaml')

    with pytest.raises(ValueError):
        args.get_artifact_value('model-source')

    assert args.get_artifact_value('input-grid-folder') == 'asset/grid'
