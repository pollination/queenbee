
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

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))

class Context():

    @property
    def config_folder(self):
        path = os.path.join(Path.home(), '.queenbee')
        os.makedirs(path, exist_ok=True)
        return path


@with_plugins(iter_entry_points('queenbee.plugins'))
@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def main(ctx):
    """ The Queenbee Resource Manager
    
    Making new things::

        queenbee operator new
        

        queenbee recipe new
    
    
    Packaging things::

        queenbee operator package PATH/TO/OPERATOR
        

        queenbee recipe package PATH/TO/RECIPE


    Checking things are ok::

        queenbee operator lint PATH/TO/OPERATOR
        

        queenbee recipe lint PATH/TO/RECIPE
   

    You can use the commands documented below to help you manage queenbee objects

    """
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


main.add_command(operator)
main.add_command(recipe)
main.add_command(repository)
