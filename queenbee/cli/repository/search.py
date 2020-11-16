import os
import json
from urllib.parse import urlparse

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )

from ...config.repositories import RepositoryReference


@click.command('search')
@click.option('-r', '--repository', help='Only search within the named repository')
@click.option('-t', '--type', 'kind', help='Only search for a certain type of package')
@click.option('-s', '--search', help='A search query')
def search(repository, kind, search):
    """search for packages inside a repository

    Use this command to search for packages inside of one of the
    repositories indexed on the user's machine.
    """
    ctx = click.get_current_context()

    packages = []

    if repository is not None:
        repos = [
            r.fetch(auth_header=ctx.obj.config.get_auth_header(
                repository_url=r.path))
            for r in ctx.obj.config.repositories if r.name == repository
        ]
    else:
        repos = [
            r.fetch(auth_header=ctx.obj.config.get_auth_header(
                repository_url=r.path))
            for r in ctx.obj.config.repositories
        ]

    for r in repos:
        packages.extend(r.search(
            kind=kind,
            search_string=search,
        ))

    exclude_keys = {
        'readme',
        'license',
        'manifest'
    }

    if packages == []:
        return print(json.dumps([]))

    print(json.dumps([p.dict(exclude=exclude_keys)
                      for p in packages], indent=2, default=packages[0].__json_encoder__))


@click.command('get')
@click.argument('type')
@click.argument('repo')
@click.argument('name')
@click.option('-t', '--tag', help='Package tag.', default='latest')
def get_by_tag(type, repo, name, tag):
    """get and print a specific package

    Use this command to print out a specific package version from a given repository.

    type: Package type. It should be either a plugin or a repository.

    repo: The name of the repository.

    name: Name of the package.

    """

    ctx = click.get_current_context()
    repo_ref = ctx.obj.config.get_repository(repo)

    if repo_ref is None:
        raise click.ClickException(f'No repository with name "{repo}" found')

    auth_header = ctx.obj.config.get_auth_header(repository_url=repo_ref.path)
    repo_index = repo_ref.fetch(auth_header=auth_header)

    try:
        package = repo_index.package_by_tag(
            kind=type,
            package_name=name,
            package_tag=tag,
        )
    except ValueError as error:
        raise click.ClickException(error)

    package = package.fetch_package(
        source_url=repo_ref.path, auth_header=auth_header)
    package.slug = f'{repo}/{package.name}'

    print(package.json(indent=2))
