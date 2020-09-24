import os
import shutil

from pydantic import ValidationError

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.command('view')
def view():
    """view the config file

    This subcommand lets you view the current config information
    """

    ctx = click.get_current_context()
    click.echo('Config location:')
    click.echo(ctx.obj.config_path)
    click.echo()
    click.echo(ctx.obj.config)
