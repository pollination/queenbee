from urllib import request
from typing import Union

from .basemodel import BaseModel

USER_AGENT_STRING = 'Queenbee'

def urljoin(*args):
    url = "/".join(map(lambda x: str(x).rstrip('/'), args))
    url.replace('\\', '/')

    return url

def make_request(url: str, auth_header: str = '') -> str:

    headers = {
        'Authorization': auth_header,
        'User-Agent': USER_AGENT_STRING
    }

    req = request.Request(url=url, headers=headers)
    return request.urlopen(req)


