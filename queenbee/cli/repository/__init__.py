from .index import index

try:
    import click
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('repository')
@click.pass_context
def main(ctx):
    """manage package repositories"""
    pass

main.add_command(index)
