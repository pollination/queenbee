import os
import io
import hashlib
import json
from datetime import datetime
from tarfile import TarInfo, TarFile
from typing import Union
from ..operator import Operator
from ..recipe import Recipe

def reset_tar(tarinfo: TarInfo) -> TarInfo:
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "0"
    return tarinfo


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
