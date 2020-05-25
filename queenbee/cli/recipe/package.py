import os

from pydantic import ValidationError

from ...recipe import Recipe, BakedRecipe
from ...repository import RecipeVersion

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

@click.command('package')
@click.argument('path', type=click.Path(exists=True))
@click.option('-d', '--destination', help='location to write the package', show_default=True, default='.', type=click.Path(exists=False))
@click.option('-f', '--force', help='Boolean toggle to overwrite existing package with same name and version', default=False, type=bool, is_flag=True)
@click.option('--no-update', help='Do not fetch fresh versions of dependencies before packaging', default=False, type=bool, is_flag=True)
def package(path, destination, force, no_update):
    """package an recipe

    This command helps you package recipes and add them to repository folders. A packaged
    recipe is essentially a gzipped version of its folder.

    You can package an recipe in a specific folder or repository by using the ``--destination``
    flag::

        queenbee recipe package path/to/my/recipe --destination path/to/my/repository/recipes

    If you do not specify a ``--repository`` the command will package the recipe in the
    directory the command is invoked from (ie: ``.``)

    You can also decide to not pull fresh dependencies in your ``.dependencies`` folder::

        queenbee recipe package path/to/my/recipe --no-update

    This will ensure that when compiling dependencies into a Baked Recipe to validate your
    recipe, the command will not wipe your ``.dependencies`` folder and overwrite with fresh
    dependencies.
    """
    path = os.path.abspath(path)
    repository = os.path.abspath(destination)
    os.chdir(path)

    # Check valid recipe
    refresh_deps = not no_update

    try:
        BakedRecipe.from_folder(folder_path=path, refresh_deps=refresh_deps)
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error

    RecipeVersion.package_folder(
        folder_path=path,
        repo_folder=repository,
        overwrite=force,
        check_deps=False,
    )
