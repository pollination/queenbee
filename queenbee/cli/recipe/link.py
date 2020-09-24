import os
import shutil

from pydantic import ValidationError

from ...recipe import Recipe, BakedRecipe

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.command('link')
@click.argument('dependency_name')
@click.argument('dependency_path', type=click.Path(exists=True))
@click.option('-r', '--recipe-path', help='Path to the recipe folder where link should be created', show_default=True, default='.', type=click.Path(exists=False))
def link(dependency_name, dependency_path, recipe_path):
    """link a local recipe/operator to a dependency of another recipe

    This subcommand helps develop recipes and operators at the same time without
    needing to update source repositories.
    """

    recipe = Recipe.from_folder(recipe_path)

    try:
        dependency = recipe.dependency_by_name(
            recipe.dependencies, dependency_name)
    except ValueError as error:
        raise click.ClickException(error)

    destination = os.path.join(
        recipe_path, '.dependencies', dependency.type, dependency_name)
    destination = os.path.abspath(destination)

    source = os.path.abspath(dependency_path)

    if os.path.exists(destination):
        if os.path.isdir(destination):
            shutil.rmtree(destination)
        else:
            os.remove(destination)

    os.makedirs(os.path.dirname(destination), exist_ok=True)

    os.symlink(source, destination)
