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
@click.option('-r', '--repository', help='Path to the repository hosting this package', default='.', type=click.Path(exists=True))
@click.option('-f', '--force', help='Boolean toggle to overwrite existing package with same name and version', default=False, type=bool, is_flag=True)
@click.option('--no-update', help='Do not fetch fresh versions of dependencies before packaging', default=False, type=bool, is_flag=True)
def package(path, repository, force, no_update):
    """package a recipe"""

    path = os.path.abspath(path)
    repository = os.path.abspath(repository)
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