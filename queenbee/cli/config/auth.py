from ...config.auth import HeaderAuth

try:
    import click
    from click_plugins import with_plugins
except ImportError:
    raise ImportError(
        'click modules not installed. Try `pip install queenbee[cli]` command.'
    )


@click.group('auth')
def auth():
    """manage queenbee configuration auth"""
    pass


@auth.group('add')
def add():
    """add auth domains and methods to your queenbee config"""
    pass

@add.command('api_token')
@click.argument('api_token')
@click.option(
    '-n',
    '--header-name',
    help='API token header name',
    show_default=True,
    default='x-pollination-token'
)
@click.option(
    '-d',
    '--domain',
    help='The domain to use this credential with',
    show_default=True,
    default='api.pollination.cloud'
)
def add_api_token(api_token, header_name, domain):
    """add an API token auth config"""
    ctx = click.get_current_context()

    auth_conf = HeaderAuth(
        domain=domain,
        header_name=header_name,
        access_token=api_token,
    )
    ctx.obj.config.add_auth(auth=auth_conf)

    ctx.obj.write_config()
    
