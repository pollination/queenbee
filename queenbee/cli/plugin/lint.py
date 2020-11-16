from pydantic import ValidationError

from ...plugin import Plugin

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.command('lint')
@click.argument('path', type=click.Path(exists=True))
def lint(path):
    """lint a plugin

    Use this command to check that a plugin folder is valid.
    """

    try:
        op = Plugin.from_folder(path)
        obj = op.to_dict()
        Plugin.parse_obj(obj)
    except ValidationError as error:
        raise click.ClickException(error)
    except FileNotFoundError as error:
        raise click.ClickException(error)
    except Exception as error:
        raise error

    click.echo('Your plugin is looking good!')
