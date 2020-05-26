"""Queenbee Operator class."""
import os
import yaml
from typing import List
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from .function import Function
from .metadata import MetaData


class DockerConfig(BaseModel):
    """Operator Configuration to run in a Docker container"""

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
    """Operator Configuration to run on a desktop."""

    pass


class Config(BaseModel):
    """Operator configuration.

    The config is used to schedule functions on a desktop or in other contexts
    (ie: Docker).
    """

    docker: DockerConfig = Field(
        ...,
        description='The configuration to use this operator in a docker container'
    )

    local: LocalConfig = Field(
        None,
        description='The configuration to use this operator locally'
    )


class Operator(BaseModel):
    """A Queenbee Operator.

    An Operator contains runtime configuration for a Command Line Interface (CLI) and
    a list of functions that can be executed using this CLI tool.
    """

    metadata: MetaData = Field(
        ...,
        description='The Operator metadata information'
    )

    config: Config = Field(
        ...,
        description='The configuration information to run this operator'
    )

    functions: List[Function] = Field(
        ...,
        description='List of Operator functions'
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
        """Generate an Operator from a folder

        Note:
            Here is an example of an Operator folder:
            ::

                .
                ├── functions
                │   ├── function-1.yaml
                │   ├── function-2.yaml
                │   ├── ....yaml
                │   └── function-n.yaml
                ├── config.yaml
                └── operator.yaml

        Arguments:
            folder_path {str} -- Path to the folder

        Returns:
            Operator -- An operator
        """
        folder_path = os.path.realpath(folder_path)
        meta_path = os.path.join(folder_path, 'operator.yaml')
        config_path = os.path.join(folder_path, 'config.yaml')
        functions_path = os.path.join(folder_path, 'functions')

        operator = {}
        functions = []

        with open(meta_path, 'r') as f:
            metadata = yaml.load(f, yaml.FullLoader)

        with open(config_path, 'r') as f:
            config = yaml.load(f, yaml.FullLoader)

        for function in os.listdir(functions_path):
            with open(os.path.join(functions_path, function), 'r') as f:
                functions.append(yaml.load(f, yaml.FullLoader))

        operator['metadata'] = metadata
        operator['config'] = config
        operator['functions'] = functions

        return cls.parse_obj(operator)

    def to_folder(self, folder_path: str):
        """Write an Operator to a folder

        Note:
            Here is an example of an Operator folder:
            ::

                .
                ├── functions
                │   ├── function-1.yaml
                │   ├── function-2.yaml
                │   ├── ....yaml
                │   └── function-n.yaml
                ├── config.yaml
                └── operator.yaml

        Arguments:
            folder_path {str} -- Path to write the folder to
        """
        os.makedirs(os.path.join(folder_path, 'functions'))

        self.metadata.to_yaml(
            os.path.join(folder_path, 'operator.yaml'),
            exclude_unset=True
        )
        self.config.to_yaml(os.path.join(folder_path, 'config.yaml'), exclude_unset=True)


        for function in self.functions:
            function.to_yaml(
                os.path.join(folder_path, 'functions', f'{function.name}.yaml'),
                exclude_unset=True
            )
