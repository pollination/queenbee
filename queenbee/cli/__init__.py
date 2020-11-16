
try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

import os
from pkg_resources import iter_entry_points

from .context import Context
from .plugin import main as plugin
from .recipe import main as recipe
from .repository import main as repository
from .config import main as config


MODULE_PATH = os.path.abspath(os.path.dirname(__file__))


@with_plugins(iter_entry_points('queenbee.plugins'))
@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def main(ctx):
    """ The Queenbee Resource Manager

    Making new things::

        queenbee plugin new


        queenbee recipe new


    Packaging things::

        queenbee plugin package PATH/TO/PLUGIN


        queenbee recipe package PATH/TO/RECIPE


    Checking things are ok::

        queenbee plugin lint PATH/TO/PLUGIN


        queenbee recipe lint PATH/TO/RECIPE


    You can use the commands documented below to help you manage queenbee objects

    """
    ctx.ensure_object(Context)

    if ctx.invoked_subcommand is None:
        with open(os.path.join(MODULE_PATH, 'assets/queenbee-art.txt'), 'r') as f:
            queenbee_art = f.read()
        click.echo(queenbee_art)
        click.echo(ctx.command.get_help(ctx))


@main.command('viz')
def viz():
    """check queenbee is flying"""
    click.echo("""

                                       .' '.            __
  viiiiiiiiiiiiizzzzzzzzz!  . .        .   .           (__\_
                               .         .         . -{{_(|8)
                                 ' .  . ' ' .  . '     (__/

    """)


main.add_command(config)
main.add_command(plugin)
main.add_command(recipe)
main.add_command(repository)
