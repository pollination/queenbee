from queenbee.schema.arguments import Arguments, Parameter, Artifact
import yaml


def test_load_arguments():
    args = Arguments.from_file('./tests/assets/arguments.yaml')

    # check parameter
    parameter = args.parameters[0]
    assert isinstance(parameter, Parameter)
    parameter.name == 'worker'
    parameter.value == 1

    # check artifact
    artifact = args.artifacts[0]
    assert isinstance(artifact, Artifact)
    artifact.name == 'project-folder'
    artifact.location == 'project-folder'
    artifact.source_path == '.'
    artifact.path == 'project'



def test_create_arguments():
    args_dict = {
        'parameters': [{'name': 'worker', 'value': 1}],
        'artifacts': [{'name': 'project-folder', 'source_path': '.', 'path': 'project', 'location': 'project-folder'}]
    }

    args = Arguments.parse_obj(args_dict)

    args_file = './tests/assets/temp/arguments.yaml'
    args.to_yaml(args_file)

    # parse the yaml file and compare the two
    with open(args_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == args.to_dict()
