from typing import List, Union
from urllib.parse import urlparse
from pydantic import Field, SecretStr

from ..base.basemodel import BaseModel
from .auth import JWTAuth, PollinationAuth
from .repositories import RepositoryReference

class Config(BaseModel):

    auth: List[Union[PollinationAuth, JWTAuth]] = Field(
        [],
        description='A list of authentication configurations for different registry domains'
    )

    repositories: List[RepositoryReference] = Field(
      [],
      description='A list of repositories used for local execution'
    )

    def get_auth_header(self, repository_url: str) -> str:
        domain = urlparse(repository_url).netloc

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

    def add_repository(self, repo: RepositoryReference, force: bool = False):
      existing_index = None

      for i, existing_repo in enumerate(self.repositories):
        if existing_repo.name == repo.name:
          existing_index = i


      if existing_index is not None:
        if force:
          self.repositories[i] = repo
          return

        raise ValueError(f'Repository with name {repo.name} already exists')

      self.repositories.append(repo)


    def get_repository(self, name: str):
      for repo in self.repositories:
        if repo.name == name:
          return repo

    def remove_repository(self, name: str):
      existing_index = None

      for i, repo in enumerate(self.repositories):
        if repo.name == name:
          existing_index = i

      del self.repositories[existing_index]


    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }