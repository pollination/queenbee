from typing import List, Union
from urllib.parse import urlparse
from pydantic import Field, SecretStr

from ..base.basemodel import BaseModel
from .auth import JWTAuth, PollinationAuth

class Config(BaseModel):

    auth: List[Union[PollinationAuth, JWTAuth]] = Field(
        [],
        description='A list of authentication configurations for different registry domains'
    )

    def get_auth_header(self, registry_url: str) -> str:
        domain = urlparse(registry_url).netloc

        res = [x for x in self.auth if x.domain == domain]

        if res == []:
            return None
        
        auth_config = res[0]

        return auth_config.auth_header

    def refresh_tokens(self):
        [auth.refresh_token() for auth in self.auth]

    def add_auth(self, auth: Union[PollinationAuth, JWTAuth]):
        found = False

        for index, existing_auth in enumerate(self.auth):
            if existing_auth.domain == auth.domain:
                found = True
                self.auth[index] = auth

        if not found:
            self.auth.append(auth)


    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }