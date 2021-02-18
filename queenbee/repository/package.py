import os
import re
import hashlib
from io import BytesIO
from datetime import datetime
from tarfile import TarInfo, TarFile
from typing import Union, Tuple, Dict

from pydantic import Field, constr

from ..plugin import Plugin
from ..recipe import Recipe, BakedRecipe

from ..base.request import make_request, urljoin, resolve_local_source
from ..base.metadata import MetaData


def reset_tar(tarinfo: TarInfo) -> TarInfo:
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = '0'
    return tarinfo


def add_to_tar(tar: TarFile, data: bytes, filename: str):
    tarinfo = TarInfo(name=filename)
    tarinfo.size = len(data)
    tarinfo.mtime = int(datetime.timestamp(datetime.utcnow()))
    tarinfo.mode = 436
    tarinfo.type = b'0'
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = '0'

    tar.addfile(tarinfo, BytesIO(data))


class PackageVersion(MetaData):
    """Package Version

    A MetaData object to distinguish a specific package version within a repository
    index.
    """
    type: constr(regex='^PackageVersion$') = 'PackageVersion'

    url: str

    created: datetime

    digest: str

    slug: str = Field(
        None,
        description='A slug of the repository name and the package name.'
    )

    kind: str = Field(
        '',
        description='The type of Queenbee package (ie: recipe or plugin)'
    )

    readme: str = Field(
        None,
        description='The README file string for this package'
    )

    manifest: Union[Recipe, Plugin] = Field(
        None,
        description="The package Recipe or Plugin manifest"
    )

    @classmethod
    def from_resource(
        cls,
        resource: Union[Plugin, Recipe],
        created: datetime = None,
        include_manifest: bool = False,
    ):
        """Generate a Package Version from a resource

        Arguments:
            resource {Union[Plugin, Recipe]} -- A resource to be versioned (plugin
                or recipe)

        Keyword Arguments:
            created {datetime} -- When version was generated (default: {None})

        Raises:
            ValueError: The resource is invalid

        Returns:
            PackageVersion -- A package version object
        """
        package_path = f'{resource.metadata.name}-{resource.metadata.tag}.tgz'

        if created is None:
            created = datetime.utcnow()

        input_dict = resource.metadata.to_dict()
        input_dict['type'] = 'PackageVersion'
        input_dict['digest'] = resource.__hash__
        input_dict['created'] = created
        input_dict['url'] = package_path

        if isinstance(resource, Plugin):
            input_dict['kind'] = 'plugin'
        elif isinstance(resource, Recipe):
            input_dict['kind'] = 'recipe'

        if include_manifest:
            input_dict['manifest'] = resource.to_dict()

        return cls.parse_obj(input_dict)

    @classmethod
    def pack_tar(cls,
                 resource: Union[Plugin, Recipe],
                 readme: str = None,
                 include_manifest: bool = False,
                 ) -> Tuple['PackageVersion', BytesIO]:
        """Package a resource into a gzipped tar archive

        Arguments:
            resource {Union[Plugin, Recipe]} -- A resource to be packaged (plugin or
                recipe)

        Keyword Arguments:
            readme {str} -- resource README.md file text if it exists
                (default: {None})

        Raises:
            ValueError: Failed to create the package

        Returns:
            PackageVersion -- A package version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """

        file_object = BytesIO()

        resource_version = cls.from_resource(resource)

        tar = TarFile.open(
            name=resource_version.url,
            mode='w:gz',
            fileobj=file_object,
        )

        resource_bytes = bytes(resource.json(
            by_alias=True, exclude_unset=False), 'utf-8')
        resource_version_bytes = bytes(resource_version.json(
            by_alias=True, exclude_unset=False), 'utf-8')

        add_to_tar(
            tar=tar,
            data=resource_bytes,
            filename='resource.json'
        )

        add_to_tar(
            tar=tar,
            data=resource_version_bytes,
            filename='version.json'
        )

        if readme is not None:
            add_to_tar(
                tar=tar,
                data=bytes(readme, 'utf-8'),
                filename='README.md'
            )

        tar.close()

        resource_version.readme = readme

        if include_manifest:
            resource_version.manifest = resource

        return resource_version, file_object

    @classmethod
    def unpack_tar(
        cls,
        tar_file: BytesIO,
        verify_digest: bool = True,
        digest: str = None
    ) -> 'PackageVersion':

        tar = TarFile.open(fileobj=tar_file)

        manifest_bytes = None
        version = None
        readme_string = None
        read_digest = None

        for member in tar.getmembers():
            if member.name == 'resource.json':
                manifest_bytes = tar.extractfile(member).read()
                read_digest = hashlib.sha256(manifest_bytes).hexdigest()

                if verify_digest:
                    read_digest == digest, \
                        ValueError(
                            f'Hash of resource.json file is different from the one'
                            f' expected from the index Expected {digest} but got'
                            f' {read_digest}'
                        )
            elif member.name == 'version.json':
                version = cls.parse_raw(tar.extractfile(member).read())
            elif member.name == 'README.md':
                readme_string = tar.extractfile(member).read().decode('utf-8')

        if manifest_bytes is None:
            raise ValueError(
                'package tar file did not contain a resource.json file so could not be'
                ' decoded.'
            )

        try:
            manifest = Plugin.parse_raw(manifest_bytes)
            version.kind = 'plugin'
        except Exception as error:
            try:
                manifest = Recipe.parse_raw(manifest_bytes)
                version.kind = 'recipe'
            except Exception as error:
                raise ValueError(
                    'Package resource.json could not be read as a Recipe or a plugin')

        version.manifest = manifest
        version.readme = readme_string
        version.digest = read_digest

        return version

    @classmethod
    def from_package(cls, package_path: str):
        """Generate a package version from a packaged resource

        Arguments:
            package_path {str} -- Path to the package

        Returns:
            PackageVersion -- A package version object
        """
        if package_path.startswith('file:'):
            file_path = resolve_local_source(package_path, as_uri=False)
        else:
            file_path = package_path.replace('\\', '/')

        with open(file_path, 'rb') as f:
            filebytes = BytesIO(f.read())

        version = cls.unpack_tar(tar_file=filebytes, verify_digest=False)

        return version

    def fetch_package(self, source_url: str = None, verify_digest: bool = True,
                      auth_header: Dict[str, str] = {}) -> 'PackageVersion':
        if source_url.startswith('file:'):
            source_path = resolve_local_source(source_url)
            package_path = os.path.join(source_path, self.url)

            return self.from_package(package_path)

        package_url = urljoin(source_url, self.url)

        res = make_request(url=package_url, auth_header=auth_header)

        filebytes = BytesIO(res.read())

        return self.unpack_tar(
            tar_file=filebytes,
            verify_digest=verify_digest,
            digest=self.digest
        )

    @staticmethod
    def read_readme(folder_path: str) -> str:
        """Infer the path to the readme within a folder and read it

        Arguments:
            folder_path {str} -- Path to the folder where a readme should be found

        Returns:
            str -- The found Readme text (or None if no readme is found)
        """
        path_to_readme = None

        readme_pattern = r'^readme\.md$'

        for file in os.listdir(folder_path):
            res = re.match(readme_pattern, file, re.IGNORECASE)
            if res is not None:
                path_to_readme = os.path.join(folder_path, file)

        if path_to_readme is not None:
            with open(path_to_readme, 'r') as f:
                return f.read()

    @classmethod
    def package_resource(cls,
                         resource: Union[Plugin, Recipe],
                         check_deps: bool = True,
                         readme: str = None
                         ) -> Tuple['PackageVersion', BytesIO]:
        """Package a Recipe or Plugin into a gzipped tar file

        Arguments:
            resource {Union[Plugin, Recipe]} -- A plugin or recipe

        Keyword Arguments:
            readme {str} -- resource README.md file text if it exists
                (default: {None})

        Returns:
            PackageVersion -- A plugin or recipe version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """

        if check_deps and isinstance(resource, Recipe):
            BakedRecipe.from_recipe(resource)

        return cls.pack_tar(
            resource=resource,
            readme=readme
        )

    @classmethod
    def package_folder(
        cls,
        resource_type: str,
        folder_path: str,
        check_deps: bool = True,
    ) -> Tuple['PackageVersion', BytesIO]:
        """Package a plugin or Recipe from its folder into a gzipped tar file

        Arguments:
            folder_path {str} -- Path to the folder where the Plugin or Recipe is defined

        Keyword Arguments:
            check_deps {bool} -- Fetch the dependencies from their source and validate
                the recipe by baking it (default: {True})

        Returns:
            PackageVersion -- A recipe or plugin version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """
        if resource_type == 'recipe':
            resource = Recipe.from_folder(folder_path=folder_path)
        elif resource_type == 'plugin':
            resource = Plugin.from_folder(folder_path=folder_path)
        else:
            raise ValueError(
                f'resource_type must be one of ["recipe", "plugin"], not: {resource_type}')

        return cls.package_resource(
            resource=resource,
            check_deps=check_deps,
            readme=cls.read_readme(folder_path)
        )

    def search_match(self, search_string: str = None) -> bool:
        """Return a boolean indicating whether the search string matches the given package

        If no search string is specified this function will return True.

        Args:
            search_string (str, optional): The search string to use. Defaults to None.

        Returns:
            bool: Whether the search string matches the package or not
        """
        if search_string is None:
            return True

        search_string = search_string.lower()

        if search_string in self.name:
            return True

        if self.keywords is not None and search_string in self.keywords:
            return True

        return False
