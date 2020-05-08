from .new import new
from .lint import lint
from .package import package
from .dependency import main as dependency

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('recipe')
@click.pass_context
def main(ctx):
    """create, lint and package recipes"""
    pass

main.add_command(new)
main.add_command(lint)
main.add_command(package)
main.add_command(dependency)
