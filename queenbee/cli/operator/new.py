import os

from ...base.parser import parse_file
from ...operator import Operator

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))


@click.command('new')
@click.argument('name')
@click.option(
    '-p',
    '--path',
    help='The path at which to create the new operator. Defaults to the current'
    ' directory if not specified.'
)
def new(name, path):
    """create a new operator folder

    Use this command to create a new operator. The folder will compile to the following
    operator definition::

        \b
        metadata:
            name: <input-name>
            version: 0.1.0
        config:
        docker:
            image: docker/whalesay:latest
            workdir: /cowsay
        functions:
        - name: say-hi
        description: Make the whale say something!
        inputs:
            parameters:
            - name: message
            default: hi
            description: What the whale will say
        command: 'cowsay {{inputs.parameters.message}} | tee /tmp/hello_world.txt'
        outputs:
            parameters:
            - name: whale-said
            path: /tmp/hello_world.txt
            artifacts:
            - name: whale-said-file
            path: /tmp/hello_world.txt

    You can indicate where you want to create the operator folder by
    specifying the ``--path`` option.
    """

    folder_path = name

    if path is not None:
        folder_path = os.path.join(path, folder_path)

    folder_path = os.path.abspath(folder_path)

    if os.path.exists(folder_path):
        raise click.ClickException(
            f'Cannot create new operator at path {folder_path} because there is'
            f' already something there'
        )

    path = os.path.join(MODULE_PATH, '../assets/new-operator.yaml')
    input_dict = parse_file(path)
    input_dict['metadata']['name'] = name

    operator = Operator.parse_obj(input_dict)

    # Create entire path to folder if it does not exist
    os.makedirs(folder_path, exist_ok=True)

    operator.to_folder(folder_path=folder_path)
