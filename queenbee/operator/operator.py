"""Queenbee Task Operator class."""
import os
import yaml
from typing import List
from pydantic import Field

from ..base.basemodel import BaseModel
from .function import Function
from .metadata import MetaData


class DockerConfig(BaseModel):

    image: str = Field(
        ...,
        description='Docker image name. Must include tag'
    )

    registry: str = Field(
        None,
        description='The container registry URLs that this container should be pulled from. Will default to Dockerhub if none is specified.'
    )

    workdir: str = Field(
        ...,
        description='The working directory the entrypoint command of the container runs in.'
        'This is used to determine where to load artifacts when running in the container.'
    )


class LocalConfig(BaseModel):

    pass


class Config(BaseModel):

    docker: DockerConfig = Field(
        ...,
        description='The configuration to use this operator in a docker container'
    )

    local: LocalConfig = Field(
        None,
        description='The configuration to use this operator locally'
    )

class Operator(BaseModel):
    """Task operator.

    A task operator includes the information for executing tasks from command line
    or in a container.
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

    @classmethod
    def from_folder(cls, folder_path: str):
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
        self.metadata.to_yaml(os.path.join(folder_path, 'operator.yaml'))
        self.config.to_yaml(os.path.join(folder_path, 'config.yaml'))

        os.mkdir(os.path.join(folder_path, 'functions'))

        for function in self.functions:
            function.to_yaml(os.path.join(folder_path, 'functions', f'{function.name}.yaml'))
