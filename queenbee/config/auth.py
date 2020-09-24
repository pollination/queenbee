import json
from enum import Enum
from urllib import request
from urllib.error import HTTPError
from typing import Union
from pydantic import Field, SecretStr


from ..base.basemodel import BaseModel
from ..base.request import make_request, USER_AGENT_STRING


class BaseAuth(BaseModel):

    domain: str = Field(
        ...,
        description='The host domain to authenticate to',
        example='api.pollination.cloud'
    )

    access_token: SecretStr = Field(
        None,
        description='A JWT token retrieved from a previous login'
    )

    @property
    def auth_header(self) -> str:
        """the auth header string for this auth model

        Returns:
            str: a bearer token auth header string
        """
        if self.access_token is None:
            return ''
        return f'Bearer {self.access_token.get_secret_value()}'

    def refresh_token(self):
        pass


class JWTAuth(BaseAuth):

    type: Enum('JWTAuth', {'type': 'jwt'}) = 'jwt'


class PollinationAuth(BaseAuth):

    type: Enum('PollinationAuth', {'type': 'pollination'}) = 'pollination'

    api_token: SecretStr = Field(
        ...,
        description='The API token to use to authenticate to Pollination'
    )

    @property
    def auth_endpoint(self):
        return f'https://{self.domain}/user/login'

    def check_cached_token(self) -> bool:
        """Check whether the cached auth token is still valid

        Raises:
            err: could not verify the token with the auth server

        Returns:
            bool: whether the token is still valid
        """
        auth_header = self.auth_header

        try:
            make_request(
                url='https://api.pollination.cloud/user',
                auth_header=auth_header
            )
        except HTTPError as err:
            if err.code >= 400 or err.code < 500:
                return False
            else:
                raise err

        return True

    def refresh_token(self):
        """Refresh the cached token if it is invalid
        """
        if self.check_cached_token():
            return

        payload = json.dumps(
            {'api_token': self.api_token.get_secret_value()}).encode('utf-8')

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

        self.access_token = SecretStr(res_data.get('access_token'))
