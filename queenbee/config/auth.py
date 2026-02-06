from typing import Dict, Literal, Union
from pydantic import Field, SecretStr

from ..base.basemodel import BaseModel


class BaseAuth(BaseModel):
    type: Literal['BaseAuth'] = 'BaseAuth'

    domain: str = Field(
        ...,
        description='The host domain to authenticate to',
        json_schema_extra={'example': 'api.pollination.solutions'}
    )

    access_token: Union[SecretStr, None] = Field(
        None,
        description='An access token for the domain.'
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
    type: Literal['HeaderAuth'] = 'HeaderAuth'

    header_name: str = Field(
        ...,
        description='The HTTP header to use'
    )

    @property
    def auth_header(self) -> Dict[str, str]:
        """the auth header string for this auth model

        Returns:
            Dict[str, str]: a header with an API token
        """
        if self.access_token is None:
            return {}
        return {self.header_name: self.access_token.get_secret_value()}


class JWTAuth(BaseAuth):
    type: Literal['JWTAuth'] = 'JWTAuth'
