import os
import io
import re
import hashlib
import json
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

    url: str

    created: datetime

    digest: str

    @classmethod
    def from_resource(cls, resource: Union[Operator, Recipe], package_path: str = None, created: datetime = None):

        if package_path is None:
            if isinstance(resource, Operator):
                base_url = 'operators'
            elif isinstance(resource, Recipe):
                base_url = 'recipes'
            else:
                raise ValueError(f'resource should be an instance of Operator or Recipe, not: {type(resource)}')

            full_name = f'{resource.metadata.name}-{resource.metadata.version}.tgz'
            package_path = os.path.join(base_url, full_name)

        if created is None:
            created = datetime.utcnow()

        input_dict = resource.metadata.to_dict()
        input_dict['digest'] = resource.__hash__
        input_dict['created'] = created
        input_dict['url'] = package_path

        return cls.parse_obj(input_dict)


    @classmethod
    def _package_resource(cls, resource, repo_folder: str, path_to_readme: str = None, overwrite: bool = False):
        
        resource_version = cls.from_resource(resource)

        resource.to_json('resource.json')
        resource_version.to_json('version.json')

        folder_path = os.path.abspath(repo_folder)

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
            tar.add(os.path.abspath(path_to_readme), arcname='README.md', filter=reset_tar)
        
        tar.close()

        # Delete original resource file
        os.remove('resource.json')
        os.remove('version.json')

        return resource_version

    @classmethod
    def from_package(cls, package_path: str):
        file_path = os.path.abspath(package_path)

        tar_file = TarFile.open(file_path)

        member = tar_file.getmember('version.json')

        version_bytes = tar_file.extractfile(member).read()   

        return cls.parse_raw(version_bytes)

    @staticmethod
    def path_to_readme(folder_path: str):
        path_to_readme = None

        readme_pattern = r'^readme\.md$'
        
        for file in os.listdir(folder_path):
            res = re.match(readme_pattern, file, re.IGNORECASE)
            if res is not None:
                path_to_readme = os.path.join(folder_path, file)

        return path_to_readme


class OperatorVersion(ResourceVersion, OperatorMetadata):

    @classmethod
    def package_resource(cls, resource: Operator, repo_folder: str, path_to_readme: str = None, overwrite: bool = False):
        return cls._package_resource(resource=resource, repo_folder=repo_folder, path_to_readme=path_to_readme, overwrite=overwrite)

    @classmethod
    def package_folder(cls, folder_path: str, repo_folder: str, overwrite: bool = True):
        resource = Operator.from_folder(folder_path=folder_path)

        return cls.package_resource(
            resource=resource,
            repo_folder=repo_folder,
            path_to_readme=cls.path_to_readme(folder_path),
            overwrite=overwrite,
        )
            


class RecipeVersion(ResourceVersion, RecipeMetadata):

    @classmethod
    def package_resource(cls, resource: Recipe, repo_folder: str, check_deps: bool = True, path_to_readme: str = None, overwrite: bool = False):
        if check_deps:
            BakedRecipe.from_recipe(resource)
        
        return cls._package_resource(resource=resource, repo_folder=repo_folder, path_to_readme=path_to_readme, overwrite=overwrite)

    @classmethod
    def package_folder(cls, folder_path: str, repo_folder: str, check_deps: bool = True, overwrite: bool = True):
        resource = Recipe.from_folder(folder_path=folder_path)

        return cls.package_resource(
            resource=resource,
            repo_folder=repo_folder,
            check_deps=check_deps,
            path_to_readme=cls.path_to_readme(folder_path),
            overwrite=overwrite,
        )
            


def package_resource(
    resource: Union[Operator, Recipe],
    folder_path: str,
    path_to_readme: str = None,
    overwrite: bool = False
) -> str:
    resource.to_json('resource.json')

    folder_path = os.path.abspath(folder_path)

    tar_path = os.path.join(
        folder_path,
        f'{resource.metadata.name}-{resource.metadata.version}.tgz'
    )

    if not overwrite:
        if os.path.isfile(tar_path):
            os.remove('resource.json')
            raise ValueError(f'Cannot overwrite file at path: {tar_path}')

    tar = TarFile.open(tar_path, 'w:gz')
    tar.add('resource.json', arcname='resource.json', filter=reset_tar)
    if path_to_readme is not None:
        tar.add(os.path.abspath(path_to_readme), arcname='README.md', filter=reset_tar)
    tar.close()

    # Delete original resource file
    os.remove('resource.json')

    return tar_path


def resource_bytes_from_package(resource_path: str, repo_path: str = '.'):
    file_path = os.path.abspath(os.path.join(repo_path, resource_path))

    tar_file = TarFile.open(file_path)

    member = tar_file.getmember('resource.json')

    return tar_file.extractfile(member).read()   


def resource_from_package(resource_path: str, repo_path: str = '.'):

    file_path = os.path.abspath(os.path.join(repo_path, resource_path))

    tar_file = TarFile.open(file_path)

    member = tar_file.getmember('resource.json')

    file_b = tar_file.extractfile(member).read()

    resource = json.loads(file_b)

    resource['created'] = datetime.fromtimestamp(member.mtime)
    resource['digest'] = hashlib.sha256(file_b).hexdigest()
    resource['url'] = resource_path

    return resource
