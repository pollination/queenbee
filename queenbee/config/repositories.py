import os
from urllib.parse import urlparse
from pydantic import Field, validator
from ..base.basemodel import BaseModel
from ..base.request import make_request, urljoin


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
        """Determine whether the path is local or remote (ie: http)"""
        parsed_path = urlparse(v)

        # If it's on the local machine
        if parsed_path.scheme == '':
            v = f'file:{v}'

        return v

    def fetch(self, auth_header: str = '') -> 'RepositoryIndex':
        """Fetch the referenced repository index

        Returns:
            RepositoryIndex: return the index from the repository reference
        """
        from ..repository import RepositoryIndex

        if self.path.startswith('file:'):
            path = self.path.split('file:')[-1]
            index_path = os.path.join(path, 'index.json')
            url = f'file:{index_path}'
        else:
            url = urljoin(self.path, 'index.json')

        res = make_request(url=url, auth_header=auth_header)

        raw_bytes = res.read()

        repo = RepositoryIndex.parse_raw(raw_bytes)

        repo.metadata.name = self.name
        repo.metadata.source = self.path

        repo.add_slugs(
            root=f'{self.name}',
            packages=repo.operator
        )

        repo.add_slugs(
            root=f'{self.name}',
            packages=repo.recipe
        )

        return repo
