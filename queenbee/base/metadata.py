"""Queenbee MetaData class.

This object provides metadata information for a package.

The specification is designed based on openapi info object:
https://swagger.io/specification/#infoObject
"""

from typing import List
from pydantic import Field

from .basemodel import BaseModel


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


class License(BaseModel):
    """License information for the Package"""
    name: str = Field(
        ...,
        description='The license name used for the package.'
    )

    url: str = Field(
        None,
        description='A URL to the license used for the package.'
    )


class MetaData(BaseModel):
    """Package metadata information."""

    name: str = Field(
        ...,
        description='Package name. Make it descriptive and helpful ;)'
    )

    tag: str = Field(
        ...,
        description='The tag of the package'
    )

    app_version: str = Field(
        None,
        description='The version of the application code underlying the manifest'
    )

    keywords: List[str] = Field(
        None,
        description='A list of keywords to search the package by'
    )

    maintainers: List[Maintainer] = Field(
        None,
        description='A list of maintainers for the package'
    )

    home: str = Field(
        None,
        description='The URL of this package\'s home page'
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
        description='Whether this package is deprecated'
    )

    description: str = Field(
        None,
        description='A description of what this package does'
    )

    license: License = Field(
        None,
        description='The license information.'
    )
