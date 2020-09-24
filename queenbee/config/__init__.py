from typing import List, Union
from urllib.parse import urlparse
from pydantic import Field, SecretStr

from ..base.basemodel import BaseModel
from .auth import JWTAuth, PollinationAuth
from .repositories import RepositoryReference


class Config(BaseModel):

    auth: List[Union[PollinationAuth, JWTAuth]] = Field(
        [],
        description='A list of authentication configurations for different repository domains'
    )

    repositories: List[RepositoryReference] = Field(
        [],
        description='A list of repositories used for local execution'
    )

    def get_auth_header(self, repository_url: str) -> str:
        """Get auth headers for the given repository url

        Args:
            repository_url (str): The url to a repository

        Returns:
            str: an authorization header string (eg: "Bearer some-jwt-token")
        """
        domain = urlparse(repository_url).netloc

        res = [x for x in self.auth if x.domain == domain]

        if res == []:
            return None

        auth_config = res[0]

        return auth_config.auth_header

    def refresh_tokens(self):
        """refresh jwt auth tokens in the config
        """
        [auth.refresh_token() for auth in self.auth]

    def add_auth(self, auth: Union[PollinationAuth, JWTAuth]):
        """add an authentication method for a specific repository domain

        Args:
            auth (Union[PollinationAuth, JWTAuth]): An authentication config object
        """
        found = False

        for index, existing_auth in enumerate(self.auth):
            if existing_auth.domain == auth.domain:
                found = True
                self.auth[index] = auth

        if not found:
            self.auth.append(auth)

    def add_repository(self, repo: RepositoryReference, force: bool = False):
        """add a repository reference to the config

        Args:
            repo (RepositoryReference): a repository source url and its given name in the config
            force (bool, optional): overwrite existing repository reference with the same name if it exsits. Defaults to False.

        Raises:
            ValueError: error thrown if the repository reference already exists and is not to be overwritten
        """
        existing_index = None

        for i, existing_repo in enumerate(self.repositories):
            if existing_repo.name == repo.name:
                existing_index = i

        if existing_index is not None:
            if force:
                self.repositories[i] = repo
                return

            raise ValueError(
                f'Repository with name {repo.name} already exists')

        self.repositories.append(repo)

    def get_repository(self, name: str) -> RepositoryReference:
        """get a repository reference by name for the config

        Returns:
            RepositoryReference: a repository reference
        """
        for repo in self.repositories:
            if repo.name == name:
                return repo

    def remove_repository(self, name: str):
        """remove a repository reference from the config

        Args:
            name (str): the name of the repository to remove
        """
        existing_index = None

        for i, repo in enumerate(self.repositories):
            if repo.name == name:
                existing_index = i

        del self.repositories[existing_index]

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }
