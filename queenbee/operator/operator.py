"""Queenbee Task Operator class."""
from typing import List
from pydantic import Field, constr

from ..base.basemodel import BaseModel
from .function import Function

class Maintainer(BaseModel):

    name: str = Field(
        ...,
        description='The name of the maintainer'
    )

    email: str = Field(
        ...,
        description='The email address of the maintainer'
    )


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
    
    name: str = Field(
        ...,
        description='Operator name. This name should be unique among all the operators'
        ' in your workflow.'
    )

    version: str = Field(
        ...,
        description='The version of the operator'
    )

    config: Config = Field(
        ...,
        description='The configuration information to run this operator'
    )

    appVersion: str = Field(
        None,
        description='The version of the app binary backing the operator (CLI tool or container)'
    )

    keywords: List[str] = Field(
        None,
        description='A list of keywords to search the operator by'
    )

    maintainers: List[Maintainer] = Field(
        None,
        description='A list of maintainers for the operator'
    )

    home: str = Field(
        None,
        description='The URL of this projects home page'
    )

    sources: List[str] = Field(
        None,
        description='A list of URLs to source code for this project'
    )

    icon: str = Field(
        None,
        description='A URL to an SVG or PNG image to be used as an icon'
    )

    deprecated: bool = Field(
        None,
        description='Whether this chart is deprecated'
    )

    description: str = Field(
        None,
        description='A description of what this operator does'
    )

    functions: List[Function]
