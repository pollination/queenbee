import os

from pydantic import ValidationError

from ...repository import OperatorVersion

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))

@click.command('package')
@click.argument('path', type=click.Path(exists=True))
@click.option('-r', '--repository', help='Path to the repository hosting this package', default='.', type=click.Path(exists=True))
@click.option('-f', '--force', help='Boolean toggle to overwrite existing package with same name and version', default=False, type=bool, is_flag=True)
def package(path, repository, force):
    """package an operator"""

    try:
        OperatorVersion.package_folder(
            folder_path=path,
            repo_folder=repository,
            overwrite=force
        )
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except ValidationError as error:
        raise error