import os
import re
import hashlib
from io import BytesIO
from datetime import datetime
from tarfile import TarInfo, TarFile
from typing import Union, Tuple

from ..operator import Operator
from ..recipe import Recipe, BakedRecipe

from ..base.basemodel import BaseModel
from ..base.request import make_request, urljoin
from ..operator.metadata import MetaData as OperatorMetadata
from ..recipe.metadata import MetaData as RecipeMetadata


def reset_tar(tarinfo: TarInfo) -> TarInfo:
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "0"
    return tarinfo

def add_to_tar(tar: TarFile, data: bytes, filename: str):
    tarinfo = TarInfo(name=filename)
    tarinfo.size = len(data)
    tarinfo.mtime = int(datetime.timestamp(datetime.utcnow()))
    tarinfo.mode = 436
    tarinfo.type = b'0'
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "0"
    
    tar.addfile(tarinfo, BytesIO(data))

class ResourceVersion(BaseModel):
    """Resource Version

    A Metadata object to distinguish a specific resource version within a repository
    index.
    """

    url: str

    created: datetime

    digest: str

    @classmethod
    def from_resource(
        cls,
        resource: Union[Operator, Recipe],
        created: datetime = None
    ):
        """Generate a Resource Version from a resource

        Arguments:
            resource {Union[Operator, Recipe]} -- A resource to be versioned (operator
                or recipe)

        Keyword Arguments:
            created {datetime} -- When version was generated (default: {None})

        Raises:
            ValueError: The resource is invalid

        Returns:
            ResourceVersion -- A resource version object
        """
        package_path = f'{resource.metadata.name}-{resource.metadata.tag}.tgz'

        if created is None:
            created = datetime.utcnow()

        input_dict = resource.metadata.to_dict()
        input_dict['digest'] = resource.__hash__
        input_dict['created'] = created
        input_dict['url'] = package_path

        return cls.parse_obj(input_dict)

    @classmethod
    def pack_tar(cls,
        resource: Union[Operator, Recipe],
        readme: str = None,
        license: str = None,
    ) -> Tuple['ResourceVersion', BytesIO]:
        """Package a resource into a gzipped tar archive

        Arguments:
            resource {Union[Operator, Recipe]} -- A resource to be packaged (operator or
                recipe)

        Keyword Arguments:
            readme {str} -- resource README.md file text if it exists
                (default: {None})
            license {str} -- resource LICENSE file text if it exists
                (default: {None})

        Raises:
            ValueError: Failed to create the package

        Returns:
            ResourceVersion -- A resource version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """

        file_object = BytesIO()

        resource_version = cls.from_resource(resource)
        
        tar = TarFile.open(
            name=resource_version.url,
            mode='w:gz',
            fileobj=file_object,
        )

        resource_bytes = bytes(resource.json(by_alias=True, exclude_unset=False), 'utf-8')
        resource_version_bytes = bytes(resource_version.json(by_alias=True, exclude_unset=False), 'utf-8')

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

        if license is not None:
            add_to_tar(
                tar=tar,
                data=bytes(license, 'utf-8'),
                filename='LICENSE'
            )

        tar.close()

        return resource_version, file_object


    @classmethod
    def unpack_tar(
        cls,
        tar_file: BytesIO,
        verify_digest: bool = True,
        digest: str = None
    ) -> Tuple['ResourceVersion', bytes, str, str, str]:

        tar = TarFile.open(fileobj=tar_file)

        manifest_bytes = None
        version = None
        readme_string = None
        license_string = None
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
            elif member.name == 'LICENSE':
                license_string = tar.extractfile(member).read().decode('utf-8')

        if manifest_bytes is None:
            raise ValueError(
                'package tar file did not contain a resource.json file so could not be'
                ' decoded.'
            )



        return version, manifest_bytes, read_digest, readme_string, license_string


    @classmethod
    def from_package(cls, package_path: str):
        """Generate a resource version from a packaged resource

        Arguments:
            package_path {str} -- Path to the package

        Returns:
            ResourceVersion -- A resource version object
        """
        file_path = os.path.normpath(os.path.abspath(package_path))

        with open(file_path, 'rb') as f:
            filebytes = BytesIO(f.read())

        tar_file = TarFile.open(file_path)

        version, *_ = cls.unpack_tar(tar_file=filebytes, verify_digest=False)

        return version

    def fetch_package(self, source_url: str = None, verify_digest: bool = True, auth_header: str = '') -> Tuple[bytes, str, str, str]:
        package_url = urljoin(source_url, self.url)

        res = make_request(url=package_url, auth_header=auth_header)

        filebytes = BytesIO(res.read())

        version, manifest_bytes, read_digest, readme_string, license_string = self.unpack_tar(
            tar_file=filebytes,
            verify_digest=verify_digest,
            digest=self.digest
        )

        return manifest_bytes, read_digest, readme_string, license_string


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

    @staticmethod
    def read_license(folder_path: str) -> str:
        """Infer the path to the license file within a folder and read it

        Arguments:
            folder_path {str} -- Path to the folder where a license file should be found

        Returns:
            str -- The found licence text (or None if no license file is found)
        """
        path_to_license = None

        license_pattern = r'^license$'

        for file in os.listdir(folder_path):
            res = re.match(license_pattern, file, re.IGNORECASE)
            if res is not None:
                path_to_license = os.path.join(folder_path, file)

        if path_to_license is not None:
            with open(path_to_license, 'r') as f:
                return f.read()


class OperatorVersion(ResourceVersion, OperatorMetadata):
    """A version of an Operator"""

    @classmethod
    def package_resource(cls,
        resource: Operator,
        readme: str = None,
        license: str = None,
    ) -> Tuple['OperatorVersion', BytesIO]:
        """Package an Operator into a gzipped tar file

        Arguments:
            resource {Operator} -- An operator

        Keyword Arguments:
            readme {str} -- resource README.md file text if it exists
                (default: {None})
            license {str} -- resource LICENSE file text if it exists
                (default: {None})

        Returns:
            OperatorVersion -- An operator version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """

        return cls.pack_tar(
            resource=resource,
            readme=readme,
            license=license,
        )

    @classmethod
    def package_folder(
        cls,
        folder_path: str,
    ) -> Tuple['OperatorVersion', BytesIO]:
        """Package an Operator from its folder into a gzipped tar file

        Arguments:
            folder_path {str} -- Path to the folder where the Operator is defined

        Returns:
            OperatorVersion -- An operator version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """
        resource = Operator.from_folder(folder_path=folder_path)

        return cls.package_resource(
            resource=resource,
            readme=cls.read_readme(folder_path),
            license=cls.read_license(folder_path),
        )


class RecipeVersion(ResourceVersion, RecipeMetadata):

    @classmethod
    def package_resource(
        cls,
        resource: Recipe,
        check_deps: bool = True,
        readme: str = None,
        license: str = None,
    ) -> Tuple['RecipeVersion', BytesIO]:
        """Package an Recipe into a gzipped tar file

        Arguments:
            resource {Recipe} -- An recipe

        Keyword Arguments:
            check_deps {bool} -- Fetch the dependencies from their source and validate
                the recipe by baking it (default: {True})
            readme {str} -- Text of the recipe README.md file if it exists
                (default: {None})
            license {str} -- Text of the resource LICENSE file if it exists
                (default: {None})

        Returns:
            RecipeVersion -- An recipe version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """
        if check_deps:
            BakedRecipe.from_recipe(resource)

        return cls.pack_tar(
            resource=resource,
            readme=readme,
            license=license,
        )

    @classmethod
    def package_folder(
        cls,
        folder_path: str,
        check_deps: bool = True,
    ) -> Tuple['RecipeVersion', BytesIO]:
        """Package an Recipe from its folder into a gzipped tar file

        Arguments:
            folder_path {str} -- Path to the folder where the Recipe is defined

        Keyword Arguments:
            check_deps {bool} -- Fetch the dependencies from their source and validate
                the recipe by baking it (default: {True})

        Returns:
            RecipeVersion -- An recipe version object
            BytesIO -- A BytesIO stream of the gzipped tar file
        """
        resource = Recipe.from_folder(folder_path=folder_path)

        return cls.package_resource(
            resource=resource,
            check_deps=check_deps,
            readme=cls.read_readme(folder_path),
            license=cls.read_license(folder_path),
        )
