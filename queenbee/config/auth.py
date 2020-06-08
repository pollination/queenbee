import json
from enum import Enum
from urllib import request
from urllib.error import HTTPError
from typing import Union
from pydantic import Field


from ..base.basemodel import BaseModel
from ..base.request import make_request, USER_AGENT_STRING


class BaseAuth(BaseModel):

    domain: str = Field(
        ...,
        description='The host domain to authenticate to',
        example='api.pollination.cloud'
    )

    access_token: str = Field(
        None,
        description='A JWT token retrieved from a previous login'
    )

    @property
    def auth_header(self):
        return f'Bearer {self.access_token}'


    def refresh_token(self):
        pass


class PollinationAuth(BaseAuth):

    type: Enum('PollinationAuth', {'type': 'pollination'})

    auth_endpoint: str = Field(
        'https://api.pollination.cloud/user/login',
        description='The authentication endpoint'
    )

    api_token: str = Field(
        ...,
        description='The API token to use to authenticate to Pollination'
    )

    def get_cached_token(self) -> str:
        
        auth_header = self.auth_header

        try:
            make_request(
                url='https://api.pollination.cloud/user',
                auth_header=auth_header
            )
        except error.HTTPError as err:
            if err.code == 401:
                return None
            else:
                raise err

        return self.access_token

    def refresh_token(self):

        cached_token = self.get_cached_token()

        if cached_token is not None:
            self.access_token = cached_token

            return

        payload = json.dumps({'api_token': self.api_token}).encode('utf-8')

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': USER_AGENT_STRING
        }

        req = request.Request(
            url=self.auth_endpoint,
            method='POST',
            data=payload
        )

        res = request.urlopen(req)

        res_data = json.loads(res.read())

        self.access_token = res_data.get('access_token')

