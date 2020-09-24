from .new import new
from .lint import lint
from .package import package
from .install import install
from .link import link

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('recipe')
@click.pass_context
def main(ctx):
    """create, lint and package recipes

    A recipe is a template used to connect multiple operator functions and
    even other recipes into a re-usable flow of actions. 

    Recipes should be written to file using a specific folder structure
    as shown below::

        \b
        .
        ├── .dependencies
        │   ├── operator
        │   │   └── operator-dep-name
        │   │       ├── functions
        │   │       │   ├── func-1.yaml
        │   │       │   ├── ...
        │   │       │   └── func-n.yaml
        │   │       ├── config.yaml
        │   │       └── operator.yaml
        │   └── recipe
        │       └── recipe-dep-name
        │           ├── .dependencies
        │           │   ├── operator
        │           │   └── recipe
        │           ├── flow
        │           │   └── main.yaml
        │           ├── dependencies.yaml
        │           └── recipe.yaml
        ├── flow
        │   └── main.yaml
        ├── dependencies.yaml
        └── recipe.yaml


    Here is an example "flow" to build and manage a recipe::

        queenbee recipe new test-recipe

    Make some changes to the recipe, add new dependencies etc... and finally
    compile it::

        queenbee recipe install test-recipe

    Check everything is working as expected::

        queenbee recipe lint test-recipe

    Finally you can package the recipe into the repository of your choice and index
    the package into your repository::

        queenbee recipe package test-recipe --repository path/to/my/repository

        queenbee repository index path/to/my/repository --skip

    Check the docs below to see all you can do with this sub-command
    """
    pass


main.add_command(new)
main.add_command(lint)
main.add_command(package)
main.add_command(install)
main.add_command(link)
