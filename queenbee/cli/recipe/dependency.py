import os

from pydantic import ValidationError

from ...recipe import Recipe

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('dependency')
@click.pass_context
def main(ctx):
    """download and update dependencies"""
    pass


@main.command('update')
@click.argument('path', type=click.Path(exists=True))
@click.option('-b', '--build', 'write', help='Download dependencies to the .dependencies folder after update',  default=False, type=bool, is_flag=True)
def update(path, write):
    """update the dependencies lock hash"""

    try:
        recipe = Recipe.from_folder(path)
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error

    for dep in recipe.dependencies:
        dep.digest = None

    os.chdir(path)

    recipe.lock_dependencies()
    
    recipe.write_dependency_lock('.')

    if write:
        recipe.write_dependencies('.')


@main.command('build')
@click.argument('path', type=click.Path(exists=True))
def build(path):
    """download dependencies and save them to the .dependencies folder"""
    
    try:
        recipe = Recipe.from_folder(path)
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error
    os.chdir(path)

    recipe.write_dependencies('.')

