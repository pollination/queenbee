import os

from pydantic import ValidationError

from ...operator import Operator

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))


@click.command('lint')
@click.argument('path', type=click.Path(exists=True))
def lint(path):
    """lint an operator

    Use this command to check that an operator folder is valid.
    """

    try:
        Operator.from_folder(path)
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error

    click.echo('Your operator is looking good!')
