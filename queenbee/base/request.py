from urllib import request
from typing import Union

from .basemodel import BaseModel

USER_AGENT_STRING = 'Queenbee'

def urljoin(*args):
    """join multiple string into a clean url

    Returns:
        str: a clean url string
    """
    url = "/".join(map(lambda x: str(x).rstrip('/'), args))
    url.replace('\\', '/')

    return url

def make_request(url: str, auth_header: str = '') -> str:
    """Fetch data from a url to a local file or using the http protocol

    Args:
        url (str): a url string to a local file or an http resource on a server
        auth_header (str, optional): an authorization header to use when making the request. Defaults to ''.

    Returns:
        str: [description]
    """
    headers = {
        'Authorization': auth_header,
        'User-Agent': USER_AGENT_STRING
    }

    req = request.Request(url=url, headers=headers)
    return request.urlopen(req)


