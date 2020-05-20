import os
import re
from datetime import datetime
from tarfile import TarInfo, TarFile
from typing import Union

from ..operator import Operator
from ..recipe import Recipe, BakedRecipe

from ..base.basemodel import BaseModel
from ..operator.metadata import MetaData as OperatorMetadata
from ..recipe.metadata import MetaData as RecipeMetadata


def reset_tar(tarinfo: TarInfo) -> TarInfo:
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "0"
    return tarinfo


class ResourceVersion(BaseModel):
    """Resource Version

    A Metadata object to distinguish a specific resource version within a repository
    index.
    """

    url: str

    created: datetime

    digest: str

    @classmethod
    def from_resource(cls, resource: Union[Operator, Recipe], package_path: str = None,
                      created: datetime = None):
        """Generate a Resource Version from a resource

        Arguments:
            resource {Union[Operator, Recipe]} -- A resource to be versioned (operator
                or recipe)

        Keyword Arguments:
            package_path {str} -- The path to the packaged resource manifest, will be
                ``<resource-name>-<resource_version>.tgz`` if not specified (default:
                {None})
            created {datetime} -- When version was generated (default: {None})

        Raises:
            ValueError: The resource is invalid

        Returns:
            ResourceVersion -- A resource version object
        """
        if package_path is None:
            package_path = f'{resource.metadata.name}-{resource.metadata.version}.tgz'

        if created is None:
            created = datetime.utcnow()

        input_dict = resource.metadata.to_dict()
        input_dict['digest'] = resource.__hash__
        input_dict['created'] = created
        input_dict['url'] = package_path

        return cls.parse_obj(input_dict)

    @classmethod
    def _package_resource(cls, resource: Union[Operator, Recipe], repo_folder: str,
                          path_to_readme: str = None, overwrite: bool = False):
        """Package a resource into a gzipped tar archive

        Arguments:
            resource {Union[Operator, Recipe]} -- A resource to be packaged (operator or
                recipe)
            repo_folder {str} -- Path to the repository folder

        Keyword Arguments:
            path_to_readme {str} -- Path to the resource README.md file if it exists
                (default: {None})
            overwrite {bool} -- Overwrite a package with the same name (default: {False})

        Raises:
            ValueError: Failed to create the package

        Returns:
            ResourceVersion -- A resource version object
        """
        resource_version = cls.from_resource(resource)

        resource.to_json('resource.json')
        resource_version.to_json('version.json')

        folder_path = os.path.abspath(repo_folder)

        os.makedirs(folder_path, exist_ok=True)

        tar_path = os.path.join(
            folder_path,
            resource_version.url
        )

        tar_dir = os.path.dirname(tar_path)

        os.makedirs(tar_dir, exist_ok=True)

        if not overwrite:
            if os.path.isfile(tar_path):
                os.remove('resource.json')
                raise ValueError(f'Cannot overwrite file at path: {tar_path}')

        tar = TarFile.open(tar_path, 'w:gz')
        tar.add('resource.json', arcname='resource.json', filter=reset_tar)
        tar.add('version.json', arcname='version.json', filter=reset_tar)

        if path_to_readme is not None:
            tar.add(
                os.path.abspath(path_to_readme), arcname='README.md',
                filter=reset_tar
            )

        tar.close()

        # Delete original resource file
        os.remove('resource.json')
        os.remove('version.json')

        return resource_version

    @classmethod
    def from_package(cls, package_path: str):
        """Generate a resource version from a packaged resource

        Arguments:
            package_path {str} -- Path to the package

        Returns:
            ResourceVersion -- A resource version object
        """
        file_path = os.path.normpath(os.path.abspath(package_path))

        tar_file = TarFile.open(file_path)

        member = tar_file.getmember('version.json')

        version_bytes = tar_file.extractfile(member).read()

        cls_ = cls.parse_raw(version_bytes)

        # add subfolder (e.g. operators, recipes ) to url
        cls_.url = '/'.join(file_path.split(os.sep)[-2:])

        return cls_

    @staticmethod
    def path_to_readme(folder_path: str) -> str:
        """Infer the path to the readme within a folder

        Arguments:
            folder_path {str} -- Path to the folder where a readme should be found

        Returns:
            str -- Path to the found readme (or None if no readme is found)
        """
        path_to_readme = None

        readme_pattern = r'^readme\.md$'

        for file in os.listdir(folder_path):
            res = re.match(readme_pattern, file, re.IGNORECASE)
            if res is not None:
                path_to_readme = os.path.join(folder_path, file)

        return path_to_readme


class OperatorVersion(ResourceVersion, OperatorMetadata):
    """A version of an Operator"""

    @classmethod
    def package_resource(cls, resource: Operator, repo_folder: str,
                         path_to_readme: str = None, overwrite: bool = False):
        """Package an Operator into a gzipped tar file

        Arguments:
            resource {Operator} -- An operator
            repo_folder {str} -- Path to the repository folder where the operator
                package is saved

        Keyword Arguments:
            path_to_readme {str} -- Path to the operator README.md file if it exists
                (default: {None})
            overwrite {bool} -- Overwrite an operator with the same name
                (default: {False})

        Returns:
            OperatorVersion -- An operator version object
        """
        return cls._package_resource(
            resource=resource, repo_folder=repo_folder,
            path_to_readme=path_to_readme, overwrite=overwrite
        )

    @classmethod
    def package_folder(cls, folder_path: str, repo_folder: str, overwrite: bool = True):
        """Package an Operator from its folder into a gzipped tar file

        Arguments:
            folder_path {str} -- Path to the folder where the Operator is defined
            repo_folder {str} -- Path to the repository folder where the operator
                package is saved

        Keyword Arguments:
            overwrite {bool} -- Overwrite an operator with the same name (default:
                {False})

        Returns:
            OperatorVersion -- An operator version object
        """
        resource = Operator.from_folder(folder_path=folder_path)

        return cls.package_resource(
            resource=resource,
            repo_folder=repo_folder,
            path_to_readme=cls.path_to_readme(folder_path),
            overwrite=overwrite,
        )


class RecipeVersion(ResourceVersion, RecipeMetadata):

    @classmethod
    def package_resource(
        cls, resource: Recipe, repo_folder: str, check_deps: bool = True,
            path_to_readme: str = None, overwrite: bool = False):
        """Package an Recipe into a gzipped tar file

        Arguments:
            resource {Recipe} -- An recipe
            repo_folder {str} -- Path to the repository folder where the recipe package
                is saved

        Keyword Arguments:
            check_deps {bool} -- Fetch the dependencies from their source and validate
                the recipe by baking it (default: {True})
            path_to_readme {str} -- Path to the recipe README.md file if it exists
                (default: {None})
            overwrite {bool} -- Overwrite an recipe with the same name (default: {False})

        Returns:
            RecipeVersion -- An recipe version object
        """
        if check_deps:
            BakedRecipe.from_recipe(resource)

        return cls._package_resource(
            resource=resource, repo_folder=repo_folder, path_to_readme=path_to_readme,
            overwrite=overwrite
        )

    @classmethod
    def package_folder(cls, folder_path: str, repo_folder: str, check_deps: bool = True,
                       overwrite: bool = True):
        """Package an Recipe from its folder into a gzipped tar file

        Arguments:
            folder_path {str} -- Path to the folder where the Recipe is defined
            repo_folder {str} -- Path to the repository folder where the Recipe package
                is saved

        Keyword Arguments:
            check_deps {bool} -- Fetch the dependencies from their source and validate
                the recipe by baking it (default: {True})
            overwrite {bool} -- Overwrite an recipe with the same name (default: {False})

        Returns:
            RecipeVersion -- An recipe version object
        """
        resource = Recipe.from_folder(folder_path=folder_path)

        return cls.package_resource(
            resource=resource,
            repo_folder=repo_folder,
            check_deps=check_deps,
            path_to_readme=cls.path_to_readme(folder_path),
            overwrite=overwrite,
        )
