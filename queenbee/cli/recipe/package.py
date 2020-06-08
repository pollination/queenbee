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

    If you do not specify a ``--destination`` the command will package the recipe in the
    directory the command is invoked from (ie: ``.``)

    You can also decide to not pull fresh dependencies in your ``.dependencies`` folder::

        queenbee recipe package path/to/my/recipe --no-update

    This will ensure that when compiling dependencies into a Baked Recipe to validate your
    recipe, the command will not wipe your ``.dependencies`` folder and overwrite with fresh
    dependencies.
    """
    ctx = click.get_current_context()

    path = os.path.abspath(path)
    destination = os.path.abspath(destination)
    os.chdir(path)

    # Check valid recipe
    refresh_deps = not no_update

    if refresh_deps:
        ctx.obj.refresh_tokens()

    try:
        BakedRecipe.from_folder(folder_path=path, refresh_deps=refresh_deps, config=ctx.obj.config)
        recipe_version, file_object = RecipeVersion.package_folder(
            folder_path=path,
            check_deps=False,
        )
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error



    file_path = os.path.join(destination, recipe_version.url)

    if not force and os.path.isfile(file_path):
        raise click.ClickException(f'File already exists at path {file_path}. Use -f to overwrite it.')

    with open(file_path, 'wb') as f:
        file_object.seek(0)
        f.write(file_object.read())

    