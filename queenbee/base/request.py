import os
import pathlib
import platform
from urllib import request
from typing import Dict

USER_AGENT_STRING = 'Queenbee'


def get_uri(url):
    """Resolve uri for urls and local files."""
    if url.startswith('file://'):
        return url.replace('\\', '/')
    elif url.startswith('http://') or url.startswith('https://'):
        return url

    # a local file but is not formatted as local url
    pre = 'file:///' if platform.system() == 'Windows' else 'file://'
    return resolve_local_source(pre + url)


def resolve_local_source(path, as_uri=True):
    """Get an absolute path for a file:// or file:/// path.

    Apparently both of them are used: https://en.wikipedia.org/wiki/File_URI_scheme
    """
    sep = 'file:///' if platform.system() == 'Windows' else 'file://'

    try:
        rel_path = path.split(sep)[1]
    except IndexError:
        raise ValueError('Invalid local path: {path}')

    abs_path = os.path.abspath(rel_path)

    uri = pathlib.Path(abs_path).as_uri() if as_uri \
        else pathlib.Path(abs_path).as_posix()

    return uri


def urljoin(*args):
    """join multiple string into a clean url

    Returns:
        str: a clean url string
    """
    url = "/".join(map(lambda x: str(x).rstrip('/'), args))
    url = url.replace('\\', '/')

    return url


def make_request(url: str, auth_header: Dict[str, str] = {}) -> str:
    """Fetch data from a url to a local file or using the http protocol

    Args:
        url (str): a url string to a local file or an http resource on a server
        auth_header (str, optional): an authorization header to use when making the request. Defaults to ''.

    Returns:
        str: [description]
    """
    if auth_header is None:
        auth_header = {}

    auth_header.update({
        'User-Agent': USER_AGENT_STRING
    })

    req = request.Request(url=url, headers=auth_header)
    return request.urlopen(req)
