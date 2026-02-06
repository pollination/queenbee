"""Queenbee MetaData class.

This object provides metadata information for a package.

The specification is designed based on openapi info object:
https://swagger.io/specification/#infoObject
"""

from typing import List, Literal, Union
from pydantic import Field, AnyUrl

from .basemodel import BaseModel


class Maintainer(BaseModel):
    """Maintainer information"""
    type: Literal['Maintainer'] = 'Maintainer'

    name: str = Field(
        ...,
        description='The name of the author/maintainer person or organization.'
    )

    email: Union[str, None] = Field(
        None,
        description='The email address of the author/maintainer person or organization.'
    )


class License(BaseModel):
    """License information for the Package"""
    type: Literal['License'] = 'License'

    name: str = Field(
        ...,
        description='The license name used for the package.'
    )

    url: Union[AnyUrl, None] = Field(
        None,
        description='A URL to the license used for the package.'
    )


class MetaData(BaseModel):
    """Package metadata information."""
    type: Literal['MetaData'] = 'MetaData'

    name: str = Field(
        ...,
        description='Package name. Make it descriptive and helpful ;)'
    )

    tag: str = Field(
        ...,
        description='The tag of the package'
    )

    app_version: Union[str, None] = Field(
        None,
        description='The version of the application code underlying the manifest'
    )

    keywords: Union[List[str], None] = Field(
        None,
        description='A list of keywords to search the package by'
    )

    maintainers: Union[List[Maintainer], None] = Field(
        None,
        description='A list of maintainers for the package'
    )

    home: Union[str, None] = Field(
        None,
        description='The URL of this package\'s home page'
    )

    sources: Union[List[str], None] = Field(
        None,
        description='A list of URLs to source code for this project'
    )

    icon: Union[str, None] = Field(
        None,
        description='A URL to an SVG or PNG image to be used as an icon'
    )

    deprecated: Union[bool, None] = Field(
        None,
        description='Whether this package is deprecated'
    )

    description: Union[str, None] = Field(
        None,
        description='A description of what this package does'
    )

    license: Union[License, None] = Field(
        None,
        description='The license information.'
    )
