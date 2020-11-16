import os

from ...base.parser import parse_file
from ...plugin import Plugin

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
    help='The path at which to create the new plugin. Defaults to the current'
    ' directory if not specified.'
)
def new(name, path):
    """create a new plugin folder

    Use this command to create a new plugin. The folder will compile to the following
    plugin definition::

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
            - name: message
            type: DAGStringInput
            default: hi
            description: What the whale will say
        command: 'cowsay {{inputs.message}} | tee /tmp/hello_world.txt'
        outputs:
            - name: whale-said
            type: DAGStringOutput
            path: /tmp/hello_world.txt
            - name: whale-said-file
            type: DAGFileOutput
            path: /tmp/hello_world.txt

    You can indicate where you want to create the plugin folder by
    specifying the ``--path`` option.
    """

    folder_path = name

    if path is not None:
        folder_path = os.path.join(path, folder_path)

    folder_path = os.path.abspath(folder_path)

    if os.path.exists(folder_path):
        raise click.ClickException(
            f'Cannot create new plugin at path {folder_path} because there is'
            f' already something there'
        )

    path = os.path.join(MODULE_PATH, '../assets/new-plugin.yaml')
    input_dict = parse_file(path)
    input_dict['metadata']['name'] = name

    plugin = Plugin.parse_obj(input_dict)

    # Readme
    readme_string = f"""
    # {name} Plugin

    A Queenbee Plugin.
    """

    # Create entire path to folder if it does not exist
    os.makedirs(folder_path, exist_ok=True)

    plugin.to_folder(
        folder_path=folder_path,
        readme_string=readme_string,
    )
