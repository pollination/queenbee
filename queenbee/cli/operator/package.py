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
@click.option('-d', '--destination', help='location to write the package', show_default=True, default='.', type=click.Path(exists=False))
@click.option('-f', '--force', help='Boolean toggle to overwrite existing package with same name and version', default=False, type=bool, is_flag=True)
def package(path, destination, force):
    """package an operator

    This command helps your package operators and add them to repository folders. A
    packaged operator is essentially a gzipped version of its folder.

    You can package an operator in a specific folder or repository by using the
    ``--destination``

    flag::

        queenbee operator package path/to/my/operator --destination path/to/my/repository/operators

    If you do not specify a ``--repository`` the command will package the operator in the
    directory the command is invoked from (ie: ``.``)
    """

    try:
        OperatorVersion.package_folder(
            folder_path=path,
            repo_folder=destination,
            overwrite=force
        )
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except ValidationError as error:
        raise error
