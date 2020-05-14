import os

from ...repository import RepositoryIndex

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

MODULE_PATH = os.path.abspath(os.path.dirname(__file__))

@click.command('index')
@click.argument('path', type=click.Path(exists=True))
@click.option('-i', '--index', 'index_path', help='Path to the index file to read/write to')
@click.option('-m', '--merge', help='Merge an existing index with the contents of the folder', default=False, type=bool, is_flag=True)
@click.option('-f', '--force', help='Overwrite existing package entries is digest hash does not match', default=False, type=bool, is_flag=True)
@click.option('-s', '--skip', help='Skip any packages that would otherwise be overwritten', default=False, type=bool, is_flag=True)
def index(path, index_path, merge, force, skip):
    """index the repository folder
    
    Use this command to crawl a repository folder and update/regenerate an
    ``index.json`` file. 
    """

    if index_path is None:
        index_path = os.path.join(path, 'index.json')

    index_path = os.path.abspath(index_path)


    try:
        if not merge:
            repo_index = RepositoryIndex.from_folder(path)
        else:
            repo_index = RepositoryIndex.parse_file(index_path)
            repo_index.merge_folder(path, force, skip)
    except ValueError as error:
        raise click.ClickException(error)

    repo_index.to_json(index_path, indent=2)
