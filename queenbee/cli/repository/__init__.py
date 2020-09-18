from .index import index
from .serve import serve
from .init import init
from .manage import add, list_repos, remove
from .search import search, get_by_tag

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('repo')
@click.pass_context
def main(ctx):
    """manage package repositories

    A Queenbee repository is a folder containing packaged Operators and Recipes.
    This folder contains an Index file (``index.json``) that can be used to find specific packages
    as well as track some metadata such as version, creation date and most importantly
    the ``hash digest`` of the package.

    A repository folder should be written using a specific folder structure as
    shown below::

        \b
        .
        ├── operators
        │   ├── some-operator-1.0.0.tgz
        │   ├── some-operator-1.3.5.tgz
        │   └── another-operator-1.2.3.tgz
        ├── recipes
        │   └── my-recipe-0.0.1.tgz
        └── index.json

    You can use the commands documented below to help you manage a repository
    """
    pass


main.add_command(index)
main.add_command(serve)
main.add_command(init)
main.add_command(add)
main.add_command(list_repos)
main.add_command(remove)
main.add_command(search)
main.add_command(get_by_tag)
