import json
from enum import Enum
from urllib import request
from urllib.error import HTTPError
from typing import Union, Dict
from pydantic import Field, SecretStr, constr


from ..base.basemodel import BaseModel
from ..base.request import make_request, USER_AGENT_STRING


class BaseAuth(BaseModel):

    type: constr(regex='^BaseAuth$') = 'BaseAuth'

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
    def auth_header(self) -> Dict[str, str]:
        """the auth header string for this auth model

        Returns:
            Dict[str, str]: a bearer token auth header string
        """
        if self.access_token is None:
            return {}
        return {'Authorization': f'Bearer {self.access_token.get_secret_value()}'}

    def refresh_token(self):
        pass


class HeaderAuth(BaseAuth):

    type: Enum('JWTAuth', {'type': 'jwt'}) = 'jwt'

    header_name: str = Field(
        ...,
        description='The HTTP header to user'
    )

    @property
    def auth_header(self) -> Dict[str, str]:
        """the auth header string for this auth model

        Returns:
            Dict[str, str]: a header with an API token
        """
        return {self.header_name: self.access_token.get_secret_value()}


class JWTAuth(BaseAuth):

    type: Enum('JWTAuth', {'type': 'jwt'}) = 'jwt'


