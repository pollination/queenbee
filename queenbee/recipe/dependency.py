"""Queenbee Task Operator class."""
from enum import Enum
from pydantic import Field

from ..base.basemodel import BaseModel


class DependencyType(str, Enum):

    workflow = 'workflow'

    operator = 'operator'


class Dependency(BaseModel):
    
    type: DependencyType = Field(
        ...,
        description='The type of dependency'
    )

    name: str = Field(
        ...,
        description='Workflow name. This name should be unique among all the resources'
        ' in your resource. Use an alias if this is not the case.'
    )

    _hash: str = Field(
        None,
        alias='hash',
        description='The digest hash of the dependency when retrieved from its source.'
        ' This is locked when the resource dependencies are downloaded.'
    )

    alias: str = Field(
        None,
        description='An optional alias to refer to this dependency. Useful if the name is'
        ' already used somewhere else.'
    )

    version: str = Field(
        ...,
        description='Version of the resource.'
    )

    owner: str = Field(
        ...,
        description='The name of the owner of this resource'
    )

    source: str = Field(
        ...,
        description='URL to a repository where this resource can be found.',
        example='https://registry.pollination.cloud'
    )


    @property
    def is_locked(self):
        return self._hash is not None