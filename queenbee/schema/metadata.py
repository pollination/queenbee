"""Queenbee MetaData class.

This object provides metadata information for a workflow.

The specification is designed based on openapi info object:
https://swagger.io/specification/#infoObject
"""

from queenbee.schema.qutil import BaseModel
from pydantic import Field
from typing import List, Union


class Author(BaseModel):
    """Author information."""
    name: str = Field(
        ...,
        description='The name of the author person or organization.'
    )

    url: str = Field(
        None,
        description='The url pointing to the author information.'
    )

    email: str = Field(
        None,
        description='The email address of the author person or organization.'
    )


class License(BaseModel):
    """License information for the workflow."""
    name: str = Field(
        ...,
        description='The license name used for the workflow.'
    )

    url: str = Field(
        None,
        description='A URL to the license used for the workflow.'
    )


class MetaData(BaseModel):
    """Workflow metadata information."""
    description: str = Field(
        None,
        description='A short description of the workflow.'
    )

    author: Union[Author, List[Author]] = Field(
        None,
        description='A single author or list of workflow authors.'
    )

    license: License = Field(
        None,
        description='The license information.'
    )

    version: str = Field(
        None,
        description='The version of the workflow.'
    )
