from ...config.auth import PollinationAuth

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


@add.command('pollination')
@click.argument('api_token')
@click.option(
    '-d',
    '--domain',
    help='The domain to use this credential with',
    show_default=True,
    default='api.pollination.cloud'
)
def add_pollination(api_token, domain):
    """add a pollination auth domain"""
    ctx = click.get_current_context()

    auth_conf = PollinationAuth(
        domain=domain,
        api_token=api_token,
    )

    ctx.obj.config.add_auth(auth=auth_conf)

    ctx.obj.write_config()
