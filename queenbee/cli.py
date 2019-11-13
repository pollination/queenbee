"""
Command Line Interface (CLI) entry point for queenbee and queenbee extensions.

Use this file only to add command related to queenbee. For adding extra commands
from each extention see below.

Note:

    Do not import this module in your code directly unless you are extending the command
    line interface. For running the commands execute them from the command line or as a
    subprocess (e.g. ``subprocess.call(['queenbee', 'viz'])``)

Queenbee is using click (https://click.palletsprojects.com/en/7.x/) for creating the CLI.
You can extend the command line interface from inside each extention by following these
steps:

1. Create a ``cli.py`` file in your extension.
2. Import the ``main`` function from this ``queenbee.cli``.
3. Add your commands and command groups to main using add_command method.
4. Add ``import [your-extention].cli`` to ``__init__.py`` file to the commands are added
   to the cli when the module is loaded.

The good practice is to group all your extention commands in a command group named after
the extension. This will make the commands organized under extension namespace. For
instance commands for `queenbee-workerbee` will be called like ``queenbee workerbee [workerbee-command]``. 


.. code-block:: python

    import click
    from queenbee.cli import main

    @click.group()
    def workerbee():
        pass

    # add commands to workerbee group
    @workerbee.command('run')
    # ...
    def run():
        pass


    # finally add the newly created commands to queenbee cli
    main.add_command(workerbee)

    # do not forget to import this module in __init__.py otherwise it will not be added
    # to queenbee commands.

Note:

    For extension with several commands you can use a folder structure instead of a single
    file. Refer to ``queenbee-workerbee`` for an example.

"""

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

import webbrowser
import urllib.parse
from pkg_resources import iter_entry_points
from queenbee.schema.workflow import Workflow

# TODO: Comment out and use for logging once we are adding commands to this file.
# import logging
# logger = logging.getLogger(__name__)


class Context():

    @staticmethod
    def parse_workflow(filepath):
        try:
            wf = Workflow.from_file(filepath)
            wf.validate_all()
            return wf
        except AssertionError as e:
            raise click.UsageError(e)
        except Exception as e:
            raise click.ClickException(e)


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
    """Check if queenbee is flying!"""
    click.echo("""
    
                                       .' '.            __
  viiiiiiiiiiiiizzzzzzzzz!  . .        .   .           (__\_
                               .         .         . -{{_(|8)
                                 ' .  . ' ' .  . '     (__/

    """)


@main.command('validate')
@click.option('-f', '--file', help='path to the workflow file to validate', required=True)
@click.option('-d', '--display', help='boolean flag to display the workflow in your browser', default=False, type=bool, is_flag=True)
@click.pass_context
def validate(ctx, file, display):
    """Validate an existing workflow file"""
    wf = ctx.obj.parse_workflow(file)

    dot = wf.to_diagraph(filename=file.split('.')[0])

    click.echo("""
                       _   _
                      ( | / )
                    \\\\ \\|/,'_
                    (")(_)()))=-
Valid Workflow!        <\\\\

    """)

    if display:
        query = urllib.parse.quote(dot.pipe(format='xdot'))
        url = 'https://dreampuf.github.io/GraphvizOnline/#{}'.format(query)
        webbrowser.open(url)


if __name__ == "__main__":
    main()
