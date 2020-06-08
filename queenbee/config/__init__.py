from typing import List, Union
from urllib.parse import urlparse
from pydantic import Field
from ..base.basemodel import BaseModel
from .auth import PollinationAuth

class Config(BaseModel):

    auth: List[Union[PollinationAuth]] = Field(
        [],
        description='A list of authentication configurations for different registry domains'
    )

    def get_auth_header(self, registry_url: str) -> str:
        domain = urlparse(registry_url).netloc

        res = [x for x in self.auth if x.domain == domain]

        if res == []:
            return None
        
        auth_config = res[0]

        return auth_config.auth_header()