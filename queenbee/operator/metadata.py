"""Queenbee Operator MetaData class.

This object provides metadata information for an Operator.

The specification is designed based on openapi info object:
https://swagger.io/specification/#infoObject
"""

from typing import List
from pydantic import Field

from ..base.basemodel import BaseModel


class Maintainer(BaseModel):
    """Maintainer information"""
    name: str = Field(
        ...,
        description='The name of the author/maintainer person or organization.'
    )

    email: str = Field(
        None,
        description='The email address of the author/maintainer person or organization.'
    )


class MetaData(BaseModel):
    """Operator metadata information"""

    name: str = Field(
        ...,
        description='Operator name. This name should be unique among all the operators'
        ' in your workflow.'
    )

    version: str = Field(
        ...,
        description='The version of the operator'
    )

    app_version: str = Field(
        None,
        description='The version of the app binary backing the operator (CLI tool or'
        ' container)'
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
        description='The URL of this operator home page'
    )

    sources: List[str] = Field(
        None,
        description='A list of URLs to source code for this operator'
    )

    icon: str = Field(
        None,
        description='A URL to an SVG or PNG image to be used as an icon'
    )

    deprecated: bool = Field(
        None,
        description='Whether this operator is deprecated'
    )

    description: str = Field(
        None,
        description='A description of what this operator does'
    )
