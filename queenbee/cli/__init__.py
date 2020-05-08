
try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

import os
from pathlib import Path
from pkg_resources import iter_entry_points

from .operator import main as operator
from .recipe import main as recipe
from .repository import main as repository

class Context():

    @property
    def config_folder(self):
        path = os.path.join(Path.home(), '.queenbee')
        os.makedirs(path, exist_ok=True)
        return path


@with_plugins(iter_entry_points('queenbee.plugins'))
@click.group()
@click.version_option()
@click.pass_context
def main(ctx):
    """
    \b
                   ____                        ____            
    _  _          / __ \\                      |  _ \\           
   | )/ )        | |  | |_   _  ___  ___ _ __ | |_) | ___  ___ 
\\\\ |//,' __      | |  | | | | |/ _ \\/ _ \\ '_ \\|  _ < / _ \\/ _ \\
(")(_)-"()))=-   | |__| | |_| |  __/  __/ | | | |_) |  __/  __/
   (\\\\            \\___\\_\\\\__,_|\\___|\\___|_| |_|____/ \\___|\\___|


    """
    ctx.obj = Context()


@main.command('viz')
def viz():
    """check queenbee is flying"""
    click.echo("""
    
                                       .' '.            __
  viiiiiiiiiiiiizzzzzzzzz!  . .        .   .           (__\_
                               .         .         . -{{_(|8)
                                 ' .  . ' ' .  . '     (__/

    """)


main.add_command(operator)
main.add_command(recipe)
main.add_command(repository)
