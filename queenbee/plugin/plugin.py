"""Queenbee Plugin class."""
import json
import os
import yaml
from typing import List
from pydantic import Field, validator, constr

from ..base.basemodel import BaseModel
from ..base.metadata import MetaData
from .function import Function


class DockerConfig(BaseModel):
    """Plugin Configuration to run in a Docker container"""

    type: constr(regex='^DockerConfig') = 'DockerConfig'

    image: str = Field(
        ...,
        description='Docker image name. Must include tag.'
    )

    registry: str = Field(
        None,
        description='The container registry URLs that this container should be pulled'
        ' from. Will default to Dockerhub if none is specified.'
    )

    workdir: str = Field(
        ...,
        description='The working directory the entrypoint command of the container runs'
        'in. This is used to determine where to load artifacts when running in the '
        'container.'
    )


class LocalConfig(BaseModel):
    """Plugin Configuration to run on a desktop."""

    type: constr(regex='^LocalConfig') = 'LocalConfig'


class PluginConfig(BaseModel):
    """Plugin configuration.

    The config is used to schedule functions on a desktop or in other contexts
    (ie: Docker).
    """
    type: constr(regex='^PluginConfig') = 'PluginConfig'

    docker: DockerConfig = Field(
        ...,
        description='The configuration to use this plugin in a docker container'
    )

    local: LocalConfig = Field(
        None,
        description='The configuration to use this plugin locally'
    )


class Plugin(BaseModel):
    """A Queenbee Plugin.

    A plugin contains runtime configuration for a Command Line Interface (CLI) and
    a list of functions that can be executed using this CLI tool.
    """
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^Plugin') = 'Plugin'

    metadata: MetaData = Field(
        ...,
        description='The Plugin metadata information'
    )

    config: PluginConfig = Field(
        ...,
        description='The configuration information to run this plugin'
    )

    functions: List[Function] = Field(
        ...,
        description='List of Plugin functions'
    )

    @validator('functions')
    def sort_list(cls, v: list) -> list:
        """Sort functions list by name

        Arguments:
            v {list} -- Unsorted list of functions

        Returns:
            list -- Sorted list of functions
        """
        v.sort(key=lambda x: x.name)
        return v

    @classmethod
    def from_folder(cls, folder_path: str):
        """Generate a plugin from a folder

        Note:
            Here is an example of a plugin folder:
            ::

                .
                ├── functions
                │   ├── function-1.yaml
                │   ├── function-2.yaml
                │   ├── ....yaml
                │   └── function-n.yaml
                ├── config.yaml
                └── package.yaml

        Arguments:
            folder_path {str} -- Path to the folder

        Returns:
            Plugin -- A plugin
        """
        folder_path = os.path.realpath(folder_path)
        meta_path = os.path.join(folder_path, 'package.yaml')
        config_path = os.path.join(folder_path, 'config.yaml')
        functions_path = os.path.join(folder_path, 'functions')

        plugin = {}
        functions = []

        with open(meta_path, 'r') as f:
            metadata = yaml.load(f, yaml.FullLoader)

        with open(config_path, 'r') as f:
            config = yaml.load(f, yaml.FullLoader)

        for function in os.listdir(functions_path):
            with open(os.path.join(functions_path, function), 'r') as f:
                functions.append(yaml.load(f, yaml.FullLoader))

        plugin['metadata'] = metadata
        plugin['config'] = config
        plugin['functions'] = functions

        return cls.parse_obj(plugin)

    def to_folder(self, folder_path: str, *, readme_string: str = None):
        """Write a plugin to a folder

        Note:
            Here is an example of a plugin folder:
            ::

                .
                ├── functions
                │   ├── function-1.yaml
                │   ├── function-2.yaml
                │   ├── ....yaml
                │   └── function-n.yaml
                ├── config.yaml
                └── package.yaml

        Arguments:
            folder_path {str} -- Path to write the folder to

        Keyword Arguments:
            readme_string {str} -- The README file string (default: {None})
        """
        os.makedirs(os.path.join(folder_path, 'functions'), exist_ok=True)

        self.metadata.to_yaml(
            os.path.join(folder_path, 'package.yaml'),
            exclude_unset=False
        )
        self.config.to_yaml(os.path.join(
            folder_path, 'config.yaml'), exclude_unset=False)

        for function in self.functions:
            function.to_yaml(
                os.path.join(folder_path, 'functions',
                             f'{function.name}.yaml'),
                exclude_unset=False
            )

        if readme_string is not None:
            with open(os.path.join(folder_path, 'README.md'), 'w') as f:
                f.write(readme_string)

        with open(os.path.join(folder_path, 'LICENSE'), 'w') as f:
            f.write('To see the license for this package refer to package.yaml')
