import os
import json

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

from ...config.repositories import RepositoryReference
from ...repository.index import RepositoryIndex, RepositoryMetadata


@click.command('add')
@click.argument('name')
@click.argument('path')
@click.option('-f', '--force', help='Boolean toggle to overwrite existing repository with same name', default=False, type=bool, is_flag=True)
def add(name, path, force):
    """add a package repository

    Use this command to add a repository to your local index. This
    is useful to search, develop and use queenbee packages locally.
    """
    ctx = click.get_current_context()

    try:
        ctx.obj.config.add_repository(
            repo=RepositoryReference(name=name, path=path)
        )
    except ValueError as error:
        click.ClickException(error)

    ctx.obj.write_config()


@click.command('list')
def list_repos():
    """list the repositories saved in your local index"""
    ctx = click.get_current_context()

    repos = [
        r.fetch(auth_header=ctx.obj.config.get_auth_header(repository_url=r.path))
        for r in ctx.obj.config.repositories
    ]

    print(json.dumps([r.metadata.dict() for r in repos], indent=2))


@click.command('remove')
@click.argument('name')
def remove(name):
    """remove a package repository

    Use this command to remove a repository from your local index.
    """
    ctx = click.get_current_context()

    ctx.obj.config.remove_repository(
        name=name
    )

    ctx.obj.write_config()
