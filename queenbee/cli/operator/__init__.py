from .new import new
from .lint import lint
from .package import package

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('operator')
@click.pass_context
def main(ctx):
    """create, lint and package operators"""
    pass

main.add_command(new)
main.add_command(lint)
main.add_command(package)
