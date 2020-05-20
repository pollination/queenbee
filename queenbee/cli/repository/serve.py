import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))


@click.command('serve')
@click.argument('path', type=click.Path(exists=True))
@click.option('-p', '--port', 'port', help='The port to expose', default=8000, show_default=True)
@click.option('-a', '--address', 'address', help='The host addres to use', default='0.0.0.0', show_default=True)
def serve(port, address, path):
    """serve a local repository folder

    Use this command to serve a local repository. You can then use
    "http://localhost:8000" as a source url to resolve your recipe dependencies.
    """

    os.chdir(path)

    http = HTTPServer((address, 8000), SimpleHTTPRequestHandler)

    print(f'Serving HTTP on {address} port {port} (http://{address}:{port}/) ...')
    http.serve_forever()
