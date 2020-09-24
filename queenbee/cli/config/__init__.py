from .view import view
from .auth import auth

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('config')
@click.pass_context
def main(ctx):
    """manage queenbee configuration data"""
    pass


main.add_command(view)
main.add_command(auth)
