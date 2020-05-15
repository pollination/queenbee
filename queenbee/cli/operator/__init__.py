from .new import new
from .lint import lint
from .package import package

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('operator')
@click.pass_context
def main(ctx):
    """create, lint and package operators
    
    An operator defines a CLI tool into a series of functions. Each
    function templates the command line arguments and fixes where any
    file or folder (called artifact) should be stored for the command
    to run successfully.

    You can create a new operator folder by running the command below::

        queenbee operator new <operator-name>

    Operators should be written to file using a specific folder structure
    as shown below::

        \b
        operator-name
        ├── functions
        │   ├── function-1.yaml
        │   ├── function-2.yaml
        │   ├── ....yaml
        │   └── function-n.yaml
        ├── config.yaml
        └── operator.yaml

    Here is an example "flow" to build and manage a operator::

        queenbee operator new test-operator

    Make some changes to the operator, change container config etc... and finally
    Check everything is working as expected::

        queenbee operator lint test-operator

    Finally you can package the operator into the repository of your choice and index
    the package into your repository::

        queenbee operator package test-operator --repository path/to/my/repository

        queenbee repository index path/to/my/repository --skip

    Check the docs below to see all you can do with this sub-command
    """
    pass

main.add_command(new)
main.add_command(lint)
main.add_command(package)
