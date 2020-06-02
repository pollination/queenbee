"""Queenbee dependency class."""
import os
import hashlib
import tarfile
from enum import Enum
from io import BytesIO
from urllib import request
from typing import Tuple

from pydantic import Field

from ..base.basemodel import BaseModel


class DependencyType(str, Enum):

    recipe = 'recipe'

    operator = 'operator'


class Dependency(BaseModel):
    """Configuration to fetch a Recipe or Operator that another Recipe depends on."""

    type: DependencyType = Field(
        ...,
        description='The type of dependency'
    )

    name: str = Field(
        ...,
        description='Workflow name. This name should be unique among all the resources'
        ' in your resource. Use an alias if this is not the case.'
    )

    digest: str = Field(
        None,
        alias='hash',
        description='The digest hash of the dependency when retrieved from its source.'
        ' This is locked when the resource dependencies are downloaded.'
    )

    alias: str = Field(
        None,
        description='An optional alias to refer to this dependency. Useful if the name'
        ' is already used somewhere else.'
    )

    version: str = Field(
        ...,
        description='Version of the resource.'
    )

    source: str = Field(
        ...,
        description='URL to a repository where this resource can be found.',
        examples=[
            'https://registry.pollination.cloud/ladybugbot',
            'https://some-random-user.github.io/registry'
        ]
    )

    @property
    def is_locked(self) -> bool:
        """Indicates whether the dependency is locked to a specific digest.

        Returns:
            bool -- Boolean value to indicate whether the dependency is locked
        """
        return self.digest is not None

    @property
    def ref_name(self) -> str:
        """The name by which this dependency is referred to in the Recipe.

        Returns:
            str -- Either the dependency name or its alias
        """
        if self.alias is not None:
            return self.alias
        return self.name

    def _fetch_index(self):
        """Fetch the source repository index object.

        Returns:
            RepositoryIndex -- A repository index
        """
        from ..repository.index import RepositoryIndex

        if self.source.startswith('file:'):
            rel_path = self.source.split('file:')[1]

            abs_path = os.path.join(os.getcwd(), rel_path, 'index.json')

            url = f'file:{abs_path}'
        else:
            url = os.path.join(self.source, 'index.json')

        # replace \\ with / for the case of Windows
        url = url.replace('\\', '/')
        res = request.urlopen(url)
        raw_bytes = res.read()
        return RepositoryIndex.parse_raw(raw_bytes)

    def fetch(self, verifydigest: bool = True) -> Tuple[bytes, str]:
        """Fetch the dependency from its source

        Keyword Arguments:
            verifydigest {bool} -- If the dependency is locked, ensure the found
                manifest matches the saved digest (default: {True})

        Raises:
            ValueError: The dependency could not be found or was invalid

        Returns:
            Tuple[bytes, str] -- A JSON manifest of the dependency
        """

        index = self._fetch_index()

        if self.digest is None:
            package_meta = index.package_by_version(
                package_type=self.type,
                package_name=self.name,
                package_version=self.version
            )

            self.digest = package_meta.digest
        else:
            try:
                package_meta = index.package_by_digest(
                    package_type=self.type,
                    package_name=self.name,
                    package_digest=self.digest
                )
            except ValueError as error:
                # If hash does not exist then try to download
                # by version. This is in the case where some package
                # owner overwrote the version of the dependency
                if str(error) == f'No {self.type} package with name {self.name} ' \
                        'and digest {self.digest} exists in this index':
                    package_meta = index.package_by_version(
                        package_type=self.type,
                        package_name=self.name,
                        package_version=self.version
                    )

                    self.digest = package_meta.digest
                else:
                    raise error

        package_url = os.path.join(self.source, package_meta.url).replace('\\', '/')
        res = request.urlopen(package_url)

        filebytes = BytesIO(res.read())

        tar = tarfile.open(fileobj=filebytes)

        file_bytes = None
        readme_string = None
        license_string = None

        for member in tar.getmembers():
            if member.name == 'resource.json':
                file_bytes = tar.extractfile(member).read()

                if verifydigest:
                    assert hashlib.sha256(file_bytes).hexdigest() == self.digest, \
                        ValueError(
                            f'Hash of resource.json file is different from the one'
                            f' expected from the index Expected {self.digest} and got'
                            f' {hashlib.sha256(file_bytes).hexdigest()}'
                            )
                break
            
            elif member.name == 'README.md':
                readme_string = tar.extractfile(member).read().decode('utf-8')
            elif member.name == 'LICENSE':
                license_string = tar.extractfile(member).read().decode('utf-8')

        if file_bytes is None:
            raise ValueError(
                'package tar file did not contain a resource.json file so could not be'
                ' decoded.'
            )



        return file_bytes, self.digest, readme_string, license_string
