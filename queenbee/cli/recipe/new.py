import os

from ...base.parser import parse_file
from ...recipe import Recipe

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
    help='The path at which to create the new recipe. Defaults to the current directory if not specified.'
)
def new(name, path):
    """create a new recipe folder

    Use this command to create a new recipe. The folder will compile to the following
    recipe definition::

        \b
        metadata:
            name: <input-name>
            tag: 0.1.0
        dependencies:
        - kind: plugin
        name: whalesay
        tag: 0.1.0
        source: https://pollination.github.io/shed # Replace with name of repo
        flow:
        - name: main
        inputs:
            - name: thing-to-say
            type: DAGStringInput
            default: hi
            description: What the whale will say
        tasks:
        - name: say-something
            template: whalesay/say-hi
            arguments:
            - name: message
                type: TaskArgument
                from:
                  type: InputReference
                  variable: thing-to-say
            returns:
            - name: whale-said
                type: TaskReturn

        outputs:
            - name: what-the-whale-said
            type: DAGStringOutput
            from:
                type: TaskReference
                name: say-something
                variable: whale-said

    You can indicate where you want to create the recipe folder by
    specifying the ``--path`` option.
    """
    folder_path = name

    if path is not None:
        folder_path = os.path.join(path, folder_path)

    folder_path = os.path.abspath(folder_path)

    if os.path.exists(folder_path):
        raise click.ClickException(
            f'Cannot create new recipe at path {folder_path} because there is already something there')

    path = os.path.join(MODULE_PATH, '../assets/new-recipe.yaml')
    input_dict = parse_file(path)
    input_dict['metadata']['name'] = name

    recipe = Recipe.parse_obj(input_dict)

    # Readme
    readme_string = f"""
    # {name} Recipe

    A Queenbee Recipe.
    """

    # Create entire path to folder if it does not exist
    os.makedirs(folder_path, exist_ok=True)

    recipe.to_folder(
        folder_path=folder_path,
        readme_string=readme_string,
    )
