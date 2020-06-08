import os

from pydantic import ValidationError

from ...recipe import Recipe

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.command('install')
@click.argument('path', type=click.Path(exists=True))
def install(path):
    """download dependencies and save them to the .dependencies folder

    This subcommand interacts mostly with the ``dependencies.yaml`` file and
    ``.dependencies`` folder in your recipe folder.
    """
    ctx = click.get_current_context()
    ctx.obj.refresh_tokens()

    try:
        recipe = Recipe.from_folder(path)
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error
    os.chdir(path)

    recipe.lock_dependencies(config=ctx.obj.config)
    
    recipe.write_dependency_file('.')

    recipe.write_dependencies(
        folder_path='.',
        config=ctx.obj.config,
    )

