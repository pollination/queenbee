import os
from typing import Dict
from pydantic import Field, validator
from ..base.basemodel import BaseModel
from ..base.request import make_request, urljoin, get_uri


class RepositoryReference(BaseModel):

    name: str = Field(
        ...,
        description='The name of the repository'
    )

    path: str = Field(
        ...,
        description='The path to the repository'
    )

    @validator('path')
    def remote_or_local(cls, v):
        """Format local uri as needed (ie: file:///)"""
        return get_uri(v)

    def fetch(self, auth_header: Dict[str, str] = {}) -> 'RepositoryIndex':
        """Fetch the referenced repository index

        Returns:
            RepositoryIndex: return the index from the repository reference
        """
        from ..repository import RepositoryIndex

        if self.path.startswith('file:'):
            url = os.path.join(self.path, 'index.json')
        else:
            url = urljoin(self.path, 'index.json')

        res = make_request(url=url, auth_header=auth_header)

        raw_bytes = res.read()

        repo = RepositoryIndex.parse_raw(raw_bytes)

        repo.metadata.name = self.name
        repo.metadata.source = self.path

        repo.add_slugs(
            root=f'{self.name}',
            packages=repo.plugin
        )

        repo.add_slugs(
            root=f'{self.name}',
            packages=repo.recipe
        )

        return repo
