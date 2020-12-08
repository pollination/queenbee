from .new import new
from .lint import lint
from .package import package

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('plugin')
@click.pass_context
def main(ctx):
    """create, lint and package plugins

    A plugin defines a CLI tool into a series of functions. Each
    function templates the command line arguments and fixes where any
    file or folder (called artifact) should be stored for the command
    to run successfully.

    You can create a new plugin folder by running the command below::

        queenbee plugin new <plugin-name>

    Plugins should be written to file using a specific folder structure
    as shown below::

        \b
        plugin-name
        ├── functions
        │   ├── function-1.yaml
        │   ├── function-2.yaml
        │   ├── ....yaml
        │   └── function-n.yaml
        ├── config.yaml
        └── package.yaml

    Here is an example "flow" to build and manage a plugin::

        queenbee plugin new test-plugin

    Make some changes to the plugin, change container config etc... and finally
    Check everything is working as expected::

        queenbee plugin lint test-plugin

    Finally you can package the plugin into the repository of your choice and index
    the package into your repository::

        queenbee plugin package test-plugin --repository path/to/my/repository

        queenbee repository index path/to/my/repository --skip

    Check the docs below to see all you can do with this sub-command
    """
    pass


main.add_command(new)
main.add_command(lint)
main.add_command(package)
