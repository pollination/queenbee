import os

from pydantic import ValidationError
from ...recipe import Recipe, BakedRecipe

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

@click.command('lint')
@click.argument('path', type=click.Path(exists=True))
@click.option('-u', '--dependency-update', help='Fetch fresh dependencies from remote sources before running checks', default=False, type=bool, is_flag=True)
def lint(path, dependency_update):
    """lint a recipe

    Use this command to check that a recipe folder is valid.

    You can choose to refresh the dependencies saved in you ``.dependencies`` folder by
    using the ``--dependency-update`` or ``-u`` flag::

        queenbee recipe lint path/to/my/recipe -u

    Note that if you have not run the ``install`` command this operation will fail.
    """

    # TODO: add an exception catch for cases where some dependencies are missing from the deps folder

    ctx = click.get_current_context()

    if dependency_update:
        ctx.obj.refresh_tokens()

    try:
        BakedRecipe.from_folder(
            folder_path=path,
            refresh_deps=dependency_update,
            config=ctx.obj.config
        )
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error